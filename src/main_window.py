import logging
logger = logging.getLogger(__name__)
import subprocess

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QMainWindow

from settings import app_settings
from utils.type_hints import Icao24
from aircraft_widget import AircraftWidget
from aircraft_record import AircraftRecord
from utils.qt_utils import get_screen_geometry

WINDOW_TITLE = "OverFlightWindow"

class MainWindow(QMainWindow): 
    def __init__(self):
        super().__init__()
        self.widgets: dict[Icao24, AircraftWidget] = {}

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        # self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.Tool | Qt.WindowType.CoverWindow)
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setWindowTitle(WINDOW_TITLE)
        self.setGeometry(get_screen_geometry(app_settings.setup.display_name))

        self._show_mainwindow()

        app_settings.on_change("bbox_at_location", lambda _ : self.close_all_widgets())
        app_settings.on_change("display_name", lambda _ : self._move_mainwindow())


    def _show_mainwindow(self, delay:int = 0) -> None:
        QTimer.singleShot(delay, lambda: self._move_mainwindow())
        self.show()

    def _move_mainwindow(self) -> None:
        setup = app_settings.setup

        geom = get_screen_geometry(setup.display_name)
        self.setGeometry(geom)

        self.screenOrigin = geom.topLeft()
        x = self.screenOrigin.x()
        y = self.screenOrigin.y()

        if setup.operating_system == "linux":
            if setup.window_manager == "hyprland":
                output = subprocess.run(['hyprctl', 'dispatch', 'movewindowpixel', f'exact {x} {y},title:{WINDOW_TITLE}'], capture_output=True, text=True)
                message = output.stdout.strip()

        elif setup.operating_system == "windows":
            self.move(x, y)

        else:
            raise NotImplementedError("Operating system not supported.")

    def spawn_widget(self, aircraft: AircraftRecord) -> None:
        widget = AircraftWidget(self, aircraft)
        self.widgets[aircraft.state.icao24] = widget

    def update_widgets(self, aircrafts: dict[Icao24, AircraftRecord]) -> None:
        for icao24, aircraft in aircrafts.items():
            if icao24 in self.widgets:
                self.widgets[icao24].update_state(aircraft)
            elif len(self.widgets) < app_settings.setup.max_windows:
                self.spawn_widget(aircraft)

        stale_icao24s = [icao24 for icao24 in self.widgets if icao24 not in aircrafts]
        for icao24 in stale_icao24s:
            self.widgets[icao24].close()
            logger.debug(f"Stopped tracking {icao24}.")
            self.widgets.pop(icao24)

    def dead_reckon_widgets(self) -> None:
        for widget in self.widgets.values():
            widget.dead_reckon_increment()

    def close_all_widgets(self,):
        for widget in list(self.widgets.values()):
            widget.close()
        self.widgets.clear()
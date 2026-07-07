import logging
logger = logging.getLogger(__name__)

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMainWindow

from aircraft_widget import AircraftWidget
from settings import app_settings
from utils.aircraft_record import AircraftRecord
from utils.type_hints import *


class MainWindow(QMainWindow): 
    def __init__(self):
        super().__init__()
        self.widgets: dict[Icao24, AircraftWidget] = {}

        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowState(Qt.WindowState.WindowMaximized)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.show()

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

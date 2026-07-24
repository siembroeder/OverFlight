from PySide6.QtCore import QCoreApplication
import sys
import shiboken6
import subprocess

import logging
logger = logging.getLogger(__name__)

from PySide6.QtCore import Qt, QTimer
from PySide6.QtWidgets import QMainWindow

from settings import app_settings
from utils.type_hints import Icao24
from aircraft_widget import AircraftWidget
from aircraft_record import AircraftRecord
from utils.qt_utils import get_screen_geometry

WINDOW_TITLE = "OverFlightWindow"
SPAWN_DELAY:int = 0

import ctypes
import shiboken6
from pathlib import Path
from PySide6.QtWidgets import QApplication
from PySide6.QtGui import QGuiApplication, QNativeInterface

if getattr(sys, "frozen", False):
    _LIB_PATH = Path(sys.executable).parent / "libwlhelper.so"
else:
    _LIB_PATH = Path(__file__).resolve().parent.parent / "native" / "build" / "libwlhelper.so"


# _LIB_PATH = Path(__file__).resolve().parent.parent / "native" / "build" / "libwlhelper.so"
_lib = ctypes.CDLL(str(_LIB_PATH))

_lib.get_wayland_surface.argtypes = [ctypes.c_uint64]
_lib.get_wayland_surface.restype = ctypes.c_uint64

_lib.set_click_through.argtypes = [ctypes.c_uint64, ctypes.c_uint64, ctypes.c_uint64, ctypes.c_int]
_lib.set_click_through.restype = None



def get_window_ptrs(window:MainWindow) -> tuple|None:
    window_handle = window.windowHandle()
    if window_handle is None:
        logger.debug("No native window yet, can't enable click-through")
        return
    
    app = QApplication.instance()
    if app is None:
        return

    app_ptr = shiboken6.getCppPointer(app)[0]
    gui_app = shiboken6.wrapInstance(app_ptr, QGuiApplication)

    native = None
    if isinstance(gui_app, QGuiApplication):
        native = gui_app.nativeInterface()
    
    if not isinstance(native, QNativeInterface.QWaylandApplication):
        logger.debug("not running under wayland, skipping click-through")
        return

    cpp_ptr = shiboken6.getCppPointer(window_handle)[0]
    surface_ptr = _lib.get_wayland_surface(cpp_ptr)
    if surface_ptr == 0:
        logger.debug("wl_surface not ready yet")
        return

    return native, cpp_ptr, surface_ptr
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

        global SPAWN_DELAY 
        self._show_mainwindow(SPAWN_DELAY)

        self.clickthrough = -1

    def _show_mainwindow(self, delay:int = 400) -> None:
        #TODO I don't understand the spawndelay and how it works on wayland (hyprland) 0ms works better than 1000ms
        QTimer.singleShot(delay, lambda: self._move_mainwindow())
        self.show()
        # QTimer.singleShot(delay, lambda: self._toggle_click_through(action="enable")) 

    def _toggle_click_through(self, action:str = "") -> None:
        window_ptrs = get_window_ptrs(self)
        if window_ptrs is None:
            logger.debug("received empty window_ptrs, disregarding toggle event.")
            return

        native, cpp_ptr, surface_ptr = window_ptrs

        if self.clickthrough == 0 or action == "enable":
            enable = 1
            self.clickthrough = 1 
            logger.debug("enabled clickthrough")
        
        elif self.clickthrough == 1 or action == "disable":
            enable = 0
            self.clickthrough = 0
            logger.debug("disabled clickthrough")
        else:
            logger.debug("disregarding toggle event.")
            return

        _lib.set_click_through(
            native.display(),
            native.compositor(),
            surface_ptr,
            enable
        )

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
                if message != "ok":
                    global SPAWN_DELAY
                    logger.debug(f"Moving mainwindow with hyprland returns: {message}.\n\tDelay: {SPAWN_DELAY}, trying again")
                    self._show_mainwindow(delay = SPAWN_DELAY) # go again to ensure spawning on correct display

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

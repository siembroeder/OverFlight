import os
import json
import platform
import subprocess
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from main_window import MainWindow

from PySide6.QtCore import QTimer

WINDOW_READY_POLL_INTERVAL_MS = 50
WINDOW_READY_TIMEOUT_MS = 5000


def get_operating_system() -> str:
    return platform.system().lower()

def get_session_type() -> str:
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    elif os.environ.get("DISPLAY"):
        return "x11"
    else:
        raise NameError("Session not recognized")
       
def get_window_manager() -> str|None:

    # Try wmctrl (X11)
    try:
        out = subprocess.check_output(["wmctrl", "-m"], text=True)
        for line in out.splitlines():
            if line.startswith("Name:"):
                return line.split(sep=":", maxsplit=1)[1].lower().strip()

    except Exception:
        pass


    # Fallback to environment
    wm = os.environ.get("XDG_CURRENT_DESKTOP")
    if not wm:
        return None 
    
    return wm.lower().strip()

def get_hyprland_config_provider() -> str:
    output = subprocess.run(['hyprctl', 'status'], capture_output=True, text=True).stdout
    for line in output.splitlines():
        if line.startswith("configProvider:"):
            return line.split(":", maxsplit=1)[1].strip()
    return ""

def move_window_hyprland(x, y, title):
    config_provider = get_hyprland_config_provider()

    if config_provider == "conf":
        output = subprocess.run(['hyprctl', 'dispatch', 'movewindowpixel', f'exact {x} {y},title:{title}'], capture_output=True, text=True)

    elif config_provider == "lua":
        lua_expr = f'hl.dsp.window.move({{ x = {x}, y = {y}, relative = false, window = "title:{title}" }})'      

        output = subprocess.run(['hyprctl', 'dispatch', lua_expr], capture_output=True, text=True)

    else:
        raise ValueError("Only .conf and .lua hyprland backends are supported.")

def poll_until_window_ready_hyprland(elapsed_ms: int, execute_when_ready, window:MainWindow):
    if is_window_mapped("title", window.windowTitle()) or elapsed_ms >= WINDOW_READY_TIMEOUT_MS:
        execute_when_ready()
    else:
        QTimer.singleShot(
            WINDOW_READY_POLL_INTERVAL_MS,
            lambda: poll_until_window_ready_hyprland(elapsed_ms + WINDOW_READY_POLL_INTERVAL_MS, execute_when_ready, window),
        )

def is_window_mapped(field_name:str, field_value:str) -> bool:
    """ 
    field_name: eg class, pid
    field_value: eg Alacritty, 94499 
    """

    from settings.settings import app_settings # Import here to prevent circular import
    setup = app_settings.setup
    if setup.operating_system != "linux" or setup.window_manager != "hyprland":
        return True  # not applicable on this platform, assume ready

    result = subprocess.run(['hyprctl', 'clients', '-j'], capture_output=True, text=True)
    try:
        clients = json.loads(result.stdout)
    except json.JSONDecodeError:
        return False

    return any(c.get(field_name) == field_value and c.get("mapped") for c in clients)
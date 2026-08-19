
# Core Python imports
import os
import platform
import subprocess




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

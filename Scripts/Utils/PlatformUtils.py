

import os
import platform
import subprocess




def getUserPlatform() -> str:
    return platform.system().lower()


def getSessionType() -> str:
    if os.environ.get("WAYLAND_DISPLAY"):
        return "wayland"
    elif os.environ.get("DISPLAY"):
        return "x11"
    else:
        raise NameError("Session not recognized")
       

def getWindowManager():

    # Try wmctrl (X11)
    try:
        out = subprocess.check_output(["wmctrl", "-m"], text=True)
        for line in out.splitlines():
            if line.startswith("Name:"):
                return line.split(sep=":", maxsplit=1)[1].strip()

    except Exception:
        pass

    # Fallback to environment
    return os.environ.get("XDG_CURRENT_DESKTOP") or "unknown"

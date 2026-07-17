import os
import sys

import logging
logger = logging.getLogger(__name__)

from pathlib import Path
from platformdirs import user_config_dir


# define useful paths
PROJECT_ROOT = Path(__file__).resolve().parent.parent  # .../OverFlight/, for me it's ~/Documents/Overflight/, depends on where you stored the repo. 2x .parent deletes src/paths.py

ASSETS_DIR = PROJECT_ROOT / "assets"
DATA_DIR = PROJECT_ROOT / "data"

APPNAME = "overflight"



def get_base_path() -> Path:
    """
    Depending on if you're calling this with 
    1. by executing the build version, or
    2. uv run src/main.py from the project directly
    you'd want the program to find the right files on your system.
    """
    if getattr(sys, 'frozen', False):
        return Path(sys.executable).parent #.parent deletes OverFlight (executable name)
    else:
        return PROJECT_ROOT


def resource_path(*parts:str|Path) -> Path:
    return get_base_path().joinpath(*parts)


def _find_config_file(filenames:list[str], not_found_msg:str) -> str:
    for file in filenames:
        fullpath = os.path.join(user_config_dir(APPNAME), file)
        if os.path.isfile(fullpath):
            return fullpath
    
    raise NameError(not_found_msg)


def get_credentials_path(custom_credentials_path:str|None = None) -> str:
    if custom_credentials_path and os.path.isfile(custom_credentials_path):
        return custom_credentials_path

    return _find_config_file(   #TODO: change this to also allow unauthenticated users when out of credit protocol for unauthenticated users has been made
        ["credentials.json", ".credentials.json"], 
        "No credentials file found in your ~/.config/overflight directory or your custom path")


def get_settings_path(filename = "settings.yaml") -> str:
    return _find_config_file(
        [filename], 
        "No settings.yaml file found in your ~/.config/overflight directory")
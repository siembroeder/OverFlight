
# Core Python imports
import os
import sys
import logging
from logging.handlers import RotatingFileHandler

from paths import resource_path


def install_global_exception_handler(logger: logging.Logger):
    def handle_exception(exc_type, exc_value, exc_traceback):
        if issubclass(exc_type, KeyboardInterrupt):
            sys.__excepthook__(exc_type, exc_value, exc_traceback)
            return
        logger.error("", exc_info=(exc_type, exc_value, exc_traceback))

    sys.excepthook = handle_exception


def setup_logging(log_level:str):
    """
    AI generated logging module. 
    
    Creates two loggers, one that writes to terminal without timestamp and one that writes to file with timestamp.
    Any package that's used in the project should be added to the list at the end to surpress it's output that would otherwise clog the terminal.
    Warnings from those packages should still pass through.
    """
    LOG_DIR = resource_path("logs")
    os.makedirs(LOG_DIR, exist_ok=True)
    formatter_terminal = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    formatter_file    = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter_terminal)

    file_handler = RotatingFileHandler(LOG_DIR / "overflight.log", maxBytes=1_000_000, backupCount=3)
    file_handler.setFormatter(formatter_file)

    if log_level.lower() == "debug":
        level = logging.DEBUG
    elif log_level.lower() == "info":
        level = logging.INFO
    elif log_level.lower() == "warning":
        level = logging.WARNING
    elif log_level.lower() == "error":
        level = logging.ERROR
    else:
        level = logging.INFO

    logging.basicConfig(level=level, handlers=[stream_handler, file_handler])
    
    logging.getLogger("geopy").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("opensky_api").setLevel(logging.WARNING)
    logging.getLogger("FlightRadarAPI").setLevel(logging.ERROR)
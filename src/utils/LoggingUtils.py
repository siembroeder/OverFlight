
# Core Python imports
import os
import logging
from logging.handlers import RotatingFileHandler


def setupLogging(logLevel:str):
    """
    AI generated logging module. 
    
    Creates two loggers, one that writes to terminal without timestamp and one that writes to file with timestamp.
    Any package that's used in the project should be added to the list at the end to surpress it's output that would otherwise clog the terminal.
    Warnings from those packages should still pass through.
    """
    
    os.makedirs("logs", exist_ok=True)
    formatterTerminal = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    formatterFile    = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatterTerminal)

    fileHandler = RotatingFileHandler("logs/overflight.log", maxBytes=1_000_000, backupCount=3)
    fileHandler.setFormatter(formatterFile)

    if logLevel.lower() == "debug":
        level = logging.DEBUG
    elif logLevel.lower() == "info":
        level = logging.INFO
    elif logLevel.lower() == "warning":
        level = logging.WARNING
    else:
        level = logging.INFO

    logging.basicConfig(level=level, handlers=[streamHandler, fileHandler])
    
    logging.getLogger("geopy").setLevel(logging.WARNING)
    logging.getLogger("qasync").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("opensky_api").setLevel(logging.WARNING)
    logging.getLogger("FlightRadarAPI").setLevel(logging.ERROR)

# Core Python imports
import os
import logging
from logging.handlers import RotatingFileHandler


def setupLogging():
    os.makedirs("logs", exist_ok=True)
    formatterTerminal = logging.Formatter("[%(levelname)s] %(name)s: %(message)s")
    formatterFile    = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    streamHandler = logging.StreamHandler()
    streamHandler.setFormatter(formatterTerminal)

    fileHandler = RotatingFileHandler("logs/overflight.log", maxBytes=1_000_000, backupCount=3)
    fileHandler.setFormatter(formatterFile)

    logging.basicConfig(level=logging.INFO, handlers=[streamHandler, fileHandler])
    
    logging.getLogger("geopy").setLevel(logging.WARNING)
    logging.getLogger("qasync").setLevel(logging.WARNING)
    logging.getLogger("asyncio").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("opensky_api").setLevel(logging.WARNING)
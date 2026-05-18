import sys

from PySide6 import QtAsyncio
from PySide6.QtWidgets import QApplication

import logging
logger = logging.getLogger(__name__)
from utils.LoggingUtils import setupLogging
loggingLevel = "debug" # Set the logging level. Options : 'debug', 'info', 'warning', 'critical'
setupLogging(loggingLevel)

from WindowTracker import WindowTracker
from Settings import Settings
from AirTrafficController import AirTrafficController


def startOverflightApplication(controller:AirTrafficController):
    """
    Runs the asynchronous Qt application using a asyncio loop to ensure it runs forever
    """
    QtAsyncio.run(controller.run(), handle_sigint=True)

def main():
    """
    Starting point.
    
    Create the app, tracker(-settings, -controller) and schedule AirTrafficController.run() through startOverflightApplication
    All settings should be set in settings.json
    Read the README.md for more information on settings
    """
    logger.info("Starting OverFlight\n")
    
    app:QApplication = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    settings   = Settings.build()
    tracker    = WindowTracker(settings)
    controller = AirTrafficController(tracker)
    
    app.aboutToQuit.connect(tracker.CloseAllWindows)
    
    startOverflightApplication(controller)

if __name__ == "__main__":
    main()

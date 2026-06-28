import sys

from PySide6 import QtAsyncio
from PySide6.QtWidgets import QApplication

import logging
logger = logging.getLogger(__name__)
from api_handler import ApiHandler
from utils.logging_utils import setupLogging
logging_level = "debug" # Set the logging level. Options : 'debug', 'info', 'warning', 'critical', 'error'
setupLogging(logging_level)

from window_tracker import WindowTracker
from settings import Settings
from air_traffic_controller import AirTrafficController


def start_application(controller:AirTrafficController):
    """
    Runs the asynchronous Qt application using a asyncio loop to ensure it runs forever
    """
    QtAsyncio.run(controller.run(), handle_sigint=True)

def main():
    """
    Starting point.
    
    Create the app, tracker(-settings, -controller) and schedule AirTrafficController.run() through startOverflightApplication
    All settings should be set in settings.yaml
    Read the README.md for more information on settings
    """
    logger.info("Starting OverFlight\n")
    
    app:QApplication = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    settings   = Settings.build()
    api_handler = ApiHandler(settings)
    tracker    = WindowTracker(settings)
    controller = AirTrafficController(settings, api_handler, tracker)
    
    app.aboutToQuit.connect(tracker.close_all_windows)
    
    start_application(controller)

if __name__ == "__main__":
    main()

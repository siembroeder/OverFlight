import sys
import logging
logger = logging.getLogger(__name__)

from PySide6 import QtAsyncio
from PySide6.QtWidgets import QApplication

from api_handler import ApiHandler
from utils.logging_utils import setup_logging
from aircraft_tracker import AircraftTracker
from settings import Settings, app_settings
from air_traffic_controller import AirTrafficController

logging_level = "debug" # Set the logging level. Options : 'debug', 'info', 'warning', 'critical', 'error'
setup_logging(logging_level)

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

    api_handler = ApiHandler()
    tracker    = AircraftTracker()
    controller = AirTrafficController(api_handler, tracker)

    app.aboutToQuit.connect(tracker.close_all_windows)
    
    start_application(controller)

if __name__ == "__main__":
    main()

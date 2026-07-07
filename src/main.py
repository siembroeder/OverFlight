import sys
import logging

from PySide6 import QtAsyncio
from PySide6.QtWidgets import QApplication

from main_window import MainWindow
from api_handler import ApiHandler
from utils.logging_utils import setup_logging
from air_traffic_controller import AirTrafficController

logger = logging.getLogger(__name__)
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
    app.setQuitOnLastWindowClosed(True)

    window = MainWindow()
    api_handler = ApiHandler()
    controller = AirTrafficController(window=window, api_handler=api_handler)

    app.aboutToQuit.connect(window.close)
    
    start_application(controller)

if __name__ == "__main__":
    main()

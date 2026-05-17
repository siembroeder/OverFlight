import sys
import signal
import asyncio
import platform

from PySide6.QtCore import QEventLoop
from PySide6.QtWidgets import QApplication

import logging
logger = logging.getLogger(__name__)
from utils.LoggingUtils import setupLogging
loggingLevel = "debug" # Set the logging level. Options : 'debug', 'info', 'warning', 'critical'
setupLogging(loggingLevel)

from WindowTracker import WindowTracker
from Settings import Settings
from AirTrafficController import AirTrafficController


def startOverflightApplication(app: QApplication, controller:AirTrafficController):
    """
    Runs the asynchronous Qt application using a asyncio loop to ensure it runs forever
    """
    
    loop:QEventLoop  = QEventLoop(app)
    asyncio.set_event_loop(loop)

    if platform.system().lower() != "windows":
        loop.add_signal_handler(signal.SIGINT, QApplication.quit)
       
    # Ensure the program doesn't exit when all windows are closed:
    app.aboutToQuit.connect(loop.stop)
    with loop:
        asyncio.ensure_future(controller.run())
        loop.run_forever()


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

    settings = Settings.build()
    tracker       = WindowTracker(settings)
    controller        = AirTrafficController(tracker)
    
    # app.aboutToQuit.connect(tracker.CloseAllWindows)
    
    startOverflightApplication(app, controller)




if __name__ == "__main__":
    main()

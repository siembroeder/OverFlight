

# Core Python imports
import sys
import signal
import platform
import asyncio
from qasync import QEventLoop

# PyQt imports
from PyQt6.QtWidgets import QApplication

# Custom import
from Utils.LoggingUtils import setupLogging
import logging
loggingLevel = "debug" # Set the logging level. Options : 'debug', 'info', 'warning', 'critical'
setupLogging(loggingLevel)
logger = logging.getLogger(__name__)

from WindowTracker import WindowTracker
from WindowTrackerConfig import WindowTrackerConfig
from WindowTrackerRunner import WindowTrackerRunner


def startOverflightApplication(app: QApplication, runner:WindowTrackerRunner):
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
        asyncio.ensure_future(runner.run())
        loop.run_forever()


def main():
    """
    Starting point.
    
    Create the app, tracker(-config, -runner) and schedule WindowTrackerRunner.run() through startOverflightApplication
    All settings should be set in settings.json
    Read the README.md for more information on settings
    """
    logger.info("Starting OverFlight\n")
    
    app:QApplication = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)

    trackerConfig = WindowTrackerConfig.buildTrackerConfig()
    tracker       = WindowTracker(trackerConfig)
    runner        = WindowTrackerRunner(tracker)
    
    # app.aboutToQuit.connect(tracker.CloseAllWindows)
    
    startOverflightApplication(app, runner)




if __name__ == "__main__":
    main()

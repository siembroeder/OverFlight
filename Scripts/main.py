


# Core Python imports
import os
import sys
import signal
import platform
import asyncio
import logging
from logging.handlers import RotatingFileHandler
from qasync import QEventLoop

# PyQt imports
from PyQt6.QtWidgets import QApplication

# Custom import
from Utils.LoggingUtils import setupLogging
setupLogging()

from WindowTracker import WindowTracker
from WindowTrackerConfig import WindowTrackerConfig
from WindowTrackerRunner import WindowTrackerRunner


def startOverflightApplication(app: QApplication, runner:WindowTrackerRunner):
    """ spawn the windows asynchronously, wait for at least 10 seconds before api call, update locations asynchronously."""
    
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
    app:QApplication = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)


    trackerConfig = WindowTrackerConfig.loadSettings(settingsPath="Settings/settings.json")
    tracker       = WindowTracker(trackerConfig)
    runner        = WindowTrackerRunner(tracker, trackerConfig)
    startOverflightApplication(app, runner)
    
    
    
        # other info:
        # typecodes:list = getTypeCodes(statesAtLocation)
        # tracks          = getTrueTracks(statesAtLocation)
        # classifications = printClassifications(typecodes)












































if __name__ == "__main__":
    main()

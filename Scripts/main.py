
from opensky_api import OpenSkyApi, TokenManager, OpenSkyStates, OpenSkyApi, StateVector


# Core Python imports
import sys
import signal
import platform
from datetime import datetime

import asyncio
from qasync import QEventLoop

# PyQt imports
from PyQt6.QtWidgets import QApplication

# Custom import
from Mover import Mover
from WindowTracker import WindowTracker, WindowTrackerConfig
from HandlingOpenSkyStates import getBboxSize, getBboxOffset, fetchStatesInBbox


      
def startOverflightApplication(tracker:WindowTracker) -> QApplication:
    """ spawn the windows asynchronously, wait for at least 10 seconds before api call, update locations asynchronously."""
    app:QApplication = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    loop:QEventLoop  = QEventLoop(app)
    asyncio.set_event_loop(loop)

    if platform.system().lower() != "windows":
        loop.add_signal_handler(signal.SIGINT, QApplication.quit)
       
    # Ensure the program doesn't exit when all windows are closed:
    app.aboutToQuit.connect(loop.stop)
    with loop:
        asyncio.ensure_future(tracker.runTracker())
        loop.run_forever()
 
    return app # keep reference to prevent them from being garbage collected



def main():

    trackerConfig = WindowTrackerConfig.loadSettings(settingsPath="Settings/settings.json")
    tracker       = WindowTracker(trackerConfig)
    app = startOverflightApplication(tracker)
    
    
    
        # other info:
        # typecodes:list = getTypeCodes(statesAtLocation)
        # tracks          = getTrueTracks(statesAtLocation)
        # classifications = printClassifications(typecodes)












































if __name__ == "__main__":
    main()

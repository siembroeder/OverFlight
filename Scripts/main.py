
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
from CustomQtWindow import MainWindow
from WindowTracker import WindowTracker, WindowTrackerConfig
from HandlingOpenSkyStates import getBbox, fetchStatesInBbox


      
def startOverflightApplication(initialStates:list[StateVector], tracker:WindowTracker) ->QApplication:
    """ spawn the windows asynchronously, wait for 10 seconds before api call, update locations asynchronously."""
    app:QApplication = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    loop:QEventLoop  = QEventLoop(app)
    asyncio.set_event_loop(loop)

    if platform.system().lower() != "windows":
        loop.add_signal_handler(signal.SIGINT, QApplication.quit)
       
    # Ensure the program doesn't exit when all windows are closed:
    app.aboutToQuit.connect(loop.stop)
    with loop:
        asyncio.ensure_future(tracker.runTracker(initialStates))
        loop.run_forever()
 
    return app # keep reference to prevent them from being garbage collected



def main():

    api:OpenSkyApi = OpenSkyApi(token_manager=TokenManager.from_json_file("credentials.json"))


    # Set location, can be anything from jfk international airport to hilversum.
    locationName:str = "den haag"
    
    # Define a small or large bboxsize, for dutch standards anyway.
    bboxAtLocation:tuple[float, float, float, float] = getBbox(locationName, BboxSize="small")            # print(f"{bboxAtLocation=})

    # Define the mover for the users operating system/session
    mover:Mover = Mover()

    # Fetch initial states
    statesAtLocationWTimestamp:OpenSkyStates|None = fetchStatesInBbox(api, bboxAtLocation)       # timestamp = statesAtLocation.time        # print(f"Planes in bbox:\n {statesAtLocationWTimestamp}")
    
    if statesAtLocationWTimestamp:
        timestamp = statesAtLocationWTimestamp.time
        print(f"\nNew states at {datetime.fromtimestamp(timestamp).strftime("%Y-%m-%d %H:%M:%S")}")

        
        statesAtLocation:list[StateVector] = statesAtLocationWTimestamp.states
    
        # Start the app
        trackerConfig = WindowTrackerConfig.loadSettings(api, bboxAtLocation, mover, optionalSettingsPath="Settings/userDefinedTrackerSettings.json")
        tracker       = WindowTracker(trackerConfig)
        
        app = startOverflightApplication(statesAtLocation, tracker)
    
    
    
        # other info:
        # typecodes:list = getTypeCodes(statesAtLocation)
        # tracks          = getTrueTracks(statesAtLocation)
        # classifications = printClassifications(typecodes)












































if __name__ == "__main__":
    main()


from opensky_api import OpenSkyApi, OpenSkyApi, StateVector, OpenSkyStates

import sys
import signal
import subprocess
from datetime import datetime

import asyncio
from qasync import QEventLoop

from PyQt6.QtWidgets import QApplication

from customQtWindow import MainWindow
from handlingOpenSkyStates import fetchStatesInBbox



# window functions   
async def spawnWindow(state:StateVector, bboxAtLocation:tuple, windows:dict, screenName:str="eDP-1") -> None:
    """Use spawns a window titled f\"qtApp_{icao24}\" using hyprctl and qt, also stores the new window in the windows dict with icao24 as key"""
    icao24 = state.icao24
    subprocess.run(['hyprctl', 'keyword', 'windowrule', f'match:title qtApp_{icao24}, monitor {screenName}, float on'], capture_output=True)
    window = MainWindow(bboxAtLocation, (state.longitude, state.latitude), icao24, state.callsign, showOnScreenName = screenName)
    window.show()  # triggers showEvent 
    windows[icao24] = window
    await asyncio.sleep(0.5)

def windowIsOpen(icao24:str) -> bool:
    title = f"qtApp_{icao24}"
    # return any(w.windowTitle() == title for w in QApplication.topLevelWidgets())
    return any(w.windowTitle() == title and w.isVisible() for w in QApplication.topLevelWidgets())

async def fetchAndUpdateLocationsLoop(api:OpenSkyApi, bboxAtLocation:tuple, windows:dict, maxWindows:int, screenName:str="eDP-1") -> None: 
    """keep track of icao24 codes, spawn one window per code in bbox, close window if aircraft flies out of bbox"""
    while True:
        await asyncio.sleep(10) # wait for 10 seconds so not ratelimited by OpenSkyApi
        
        newStates:OpenSkyStates|None = fetchStatesInBbox(api, bboxAtLocation) 
               
        if not newStates or not newStates.states:
            continue # skip to next api call, else process exits.
        
        print(f"\nNew states at {datetime.fromtimestamp(newStates.time).strftime("%Y-%m-%d %H:%M:%S")}")
        newIcaos = {state.icao24 for state in newStates.states}
        
        for state in newStates.states:
            if state.icao24 in windows:
                if windowIsOpen(state.icao24):
                    windows[state.icao24].moveToPlaneLoc((state.longitude, state.latitude))
                else:
                    await spawnWindow(state, bboxAtLocation, windows, screenName)

            elif len(windows) < maxWindows: # if allowed spawn another window
                await spawnWindow(state, bboxAtLocation, windows, screenName=screenName) 
                
        # Remove planes that have moved out of the bbox
        for icao24 in list(windows.keys()):
            if icao24 not in newIcaos:
                windows[icao24].close()
                del windows[icao24]
    
def renderAndUpdateWindows(states:list[StateVector], bboxAtLocation:tuple, api:OpenSkyApi, maxWindows:int=3, screenName:str="eDP-1"):
    """ spawn the windows asynchronously, wait for 10 seconds before api call, update locations asynchronously."""
    app:QApplication = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    loop:QEventLoop  = QEventLoop(app)
    asyncio.set_event_loop(loop)
    loop.add_signal_handler(signal.SIGINT, QApplication.quit) # quit with CTRL+C from terminal

    windows:dict[str, MainWindow] = {}
       
       
       
    async def runApp():
        # spawn all windows for planes in bbox
        for index, state in enumerate(states[:maxWindows], start=1):
            await spawnWindow(state, bboxAtLocation, windows, screenName)
            
        # update te location of the windows / check for new/removed planes / check if windows were closed manually.
        await fetchAndUpdateLocationsLoop(api, bboxAtLocation, windows, maxWindows, screenName)   
    
    
    # Ensure the program doesn't exit when all windows are closed:
    app.aboutToQuit.connect(loop.stop)
    with loop:
        asyncio.ensure_future(runApp())
        loop.run_forever()
    
    
                 
    return app, windows # keep reference to prevent them from being garbage collected
    

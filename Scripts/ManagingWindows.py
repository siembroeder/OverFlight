
from opensky_api import OpenSkyApi, StateVector, OpenSkyStates

import sys
import time
import signal
import platform
from datetime import datetime

import asyncio
from qasync import QEventLoop

from PyQt6.QtWidgets import QApplication

from Mover import Mover
from CustomQtWindow import MainWindow
from HandlingOpenSkyStates import fetchStatesInBbox


def windowIsOpen(icao24:str) -> bool:
    title = f"qtApp_{icao24}"
    return any(w.windowTitle() == title and w.isVisible() for w in QApplication.topLevelWidgets())



class Tracker():
    def __init__(self, api:OpenSkyApi, bboxAtLocation:tuple, mover:Mover, maxWindows:int=3, screenName:str|None=None):
        self.api = api
        self.bboxAtLocation = bboxAtLocation
        self.mover = mover
        self.maxWindows = maxWindows
        self.screenName = screenName
        self.windows:dict[str, MainWindow] = {}
        self.numApiCallsSkipped = 0.0
        self.newestApiUpdateTime = 0.0

    async def spawnWindow(self, state:StateVector) -> None:
        """Use spawns a window titled f\"qtApp_{icao24}\" using hyprctl and qt, also stores the new window in the windows dict with icao24 as key"""
        icao24 = state.icao24
        
        window = MainWindow(self.bboxAtLocation, state, self.mover, showOnScreenName = self.screenName)
        window.show()  # triggers QMainWindow.showEvent() 
        self.windows[icao24] = window
        await asyncio.sleep(0.5)

    async def updateWindows(self, newStates:OpenSkyStates) -> None:
        """Spawn, update, or close windows based on current aircraft states."""
        newIcaos = {state.icao24 for state in newStates.states}

        for state in newStates.states:
            if state.icao24 in self.windows and windowIsOpen(state.icao24):
                self.windows[state.icao24].updateState(state)
            elif len(self.windows) < self.maxWindows:
                await self.spawnWindow(state)

        for icao24 in list(self.windows.keys()):
            if icao24 not in newIcaos:
                self.windows[icao24].close()
                del self.windows[icao24]

    async def fetchLocationsLoop(self, apiCallDelay:float=10.0) -> None: 
        """keep track of icao24 codes, spawn one window per code in bbox, close window if aircraft flies out of bbox"""
        while True:
            await asyncio.sleep(apiCallDelay) # wait for 10 seconds so not ratelimited by OpenSkyApi
            
            newStates:OpenSkyStates|None = fetchStatesInBbox(self.api, self.bboxAtLocation)  
            
            if not newStates or not newStates.states:
                print(f"New states are empty, continuing\n")
                self.numApiCallsSkipped += 1
                continue    # skip to next api call, else process exits.
            
            if newStates.time < self.newestApiUpdateTime: 
                print(f"New states older than previous, continuing\n")
                self.numApiCallsSkipped += 1
                continue    # skip if new timestamp older than previous timestamp
            
            if newStates.time - self.newestApiUpdateTime <= 0.95*(self.numApiCallsSkipped + 1)*apiCallDelay: # TODO: this filter shouldn't apply to new aircraft appearing in bbox
                print(f"New api call spacing too short, continuing\n")
                self.numApiCallsSkipped += 1
                continue    # skip if difference between timestamps is less than the elapsed real time
            
            self.newestApiUpdateTime = newStates.time
            self.numApiCallsSkipped  = 0.0  # reset
            
            print(f"New states at {datetime.fromtimestamp(newStates.time)}\n")
            await self.updateWindows(newStates)
  
    async def deadReckonLoop(self, dt:float=0.1) ->None:
        "Move windows in direction of true track with correct velocity every dt seconds"
        while True:
            t0 = time.monotonic()
            await asyncio.sleep(dt)
            dt = time.monotonic() - t0 # actual elapsed time
            for icao24,window in self.windows.items():
                if windowIsOpen(icao24):
                    window.deadReckonPosition(dt)
     
    async def runTracker(self, initialStates:list[StateVector]) -> None:
        # spawn all windows for planes in bbox
        for state in initialStates[:self.maxWindows]:
            await self.spawnWindow(state)
            
        # update te location of the windows / check for new/removed planes / check if windows were closed manually.        
        # await self.fetchLocationsLoop()   
        await asyncio.gather(self.fetchLocationsLoop(), self.deadReckonLoop())


      
def renderAndUpdateWindows(initialStates:list[StateVector], bboxAtLocation:tuple, api:OpenSkyApi, mover:Mover, maxWindows:int=3, screenName:str|None=None) ->tuple[QApplication,dict[str,MainWindow]]:
    """ spawn the windows asynchronously, wait for 10 seconds before api call, update locations asynchronously."""
    app:QApplication = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(False)
    
    loop:QEventLoop  = QEventLoop(app)
    asyncio.set_event_loop(loop)

    if platform.system().lower() != "windows": #
        loop.add_signal_handler(signal.SIGINT, QApplication.quit)

    windows:dict[str, MainWindow] = {}
       
       
    tracker = Tracker(api, bboxAtLocation, mover, maxWindows, screenName)
    # Ensure the program doesn't exit when all windows are closed:
    app.aboutToQuit.connect(loop.stop)
    with loop:
        # asyncio.ensure_future(runApp(states, bboxAtLocation, api, windows, mover, maxWindows, screenName))
        asyncio.ensure_future(tracker.runTracker(initialStates))
        loop.run_forever()
 
    return app, windows # keep reference to prevent them from being garbage collected
    


from opensky_api import StateVector, OpenSkyStates

# Core Python imports
import time
import asyncio
from datetime import datetime

# Custom imports
from StateFilter import StateFilter
from CustomQtWindow import MainWindow
from WindowTrackerConfig import WindowTrackerConfig
from HandlingOpenSkyStates import fetchStatesInBbox
from Utils.Helpers import windowIsOpen


type icao24 = str
        
class WindowTracker():
    def __init__(self, config:WindowTrackerConfig):
        self.config = config
        
        self.api            = config.api
        self.bboxAtLocation = config.bboxAtLocation
        
        self.maxWindows     = config.setup.maxWindows
        self.apiCallDelay   = config.apiConfig.apiCallDelay
        
        self.filter = StateFilter(config.tracking, self.api, config.setup.maxWindows)
        
        self.windows:dict[icao24, MainWindow] = {}
        self.numApiCallsSkipped = 0.0
        self.newestApiUpdateTime = 0.0

    def spawnWindow(self, state:StateVector) -> None:
        """Use spawns a window titled f\"qtApp_{state.icao24}\", also stores the  window in the windows dict with icao24 as key"""
        icao24 = state.icao24
        
        window = MainWindow(state, self.config)
        window.show()  # triggers QMainWindow.showEvent() 
        self.windows[icao24] = window
        
        # print(f"Now tracking {state.callsign}, {icao24=}")

    def updateWindows(self, newStates:list[StateVector], delete:bool = True) -> None:
        """Spawn, update, or close windows based on current aircraft states."""
        newIcaos = {state.icao24 for state in newStates}

        for state in newStates:
            if state.icao24 in self.windows and windowIsOpen(state.icao24):
                self.windows[state.icao24].updateState(state)
            elif len(self.windows) < self.maxWindows:
                self.spawnWindow(state)

        if delete:
            for icao24 in list(self.windows.keys()):
                if icao24 not in newIcaos:
                    self.windows[icao24].close()
                    print(f"Stopped tracking {icao24}")
                    del self.windows[icao24]
                
    async def fetchStatesLoop(self) -> None: 
            """keep track of icao24 codes, spawn one window per code in bbox, close window if aircraft flies out of bbox"""
            
            assert self.apiCallDelay >= 10.0, "Please select an apiCallDelay of at least 10 seconds."
            
            firstCall = True
            while True:
                if firstCall == False:
                    await asyncio.sleep(self.apiCallDelay) # wait for at least 10 seconds so not ratelimited by OpenSkyApi
                firstCall = False
                
                newStates:OpenSkyStates|None = fetchStatesInBbox(self.api, self.bboxAtLocation)  
                
                # skip to next api call if newStates empty.
                if not newStates or not newStates.states:
                    print(f"New states are empty, continuing\n")
                    self.numApiCallsSkipped += 1
                    continue    
                
                # skip if new timestamp older than previous timestamp
                if newStates.time < self.newestApiUpdateTime: 
                    print(f"New states older than previous, continuing\n")
                    self.numApiCallsSkipped += 1
                    continue    
                
                # skip if difference between timestamps is less than the elapsed real time. Factor 0.9 to accept decent newStates
                if newStates.time - self.newestApiUpdateTime <= 0.9*(self.numApiCallsSkipped + 1)*self.apiCallDelay:
                    
                    # If there are previously untracked states in the newest api call result, add those to tracked states. Even if the spacing is too short.
                    untrackedStates = self.filter.extractUntrackedStates(self.windows, newStates.states)
                    self.updateWindows(untrackedStates, delete = False)
                                        
                    print(f"New api call spacing too short, continuing\n")
                    self.numApiCallsSkipped += 1
                    continue    
                
                self.newestApiUpdateTime = newStates.time
                self.numApiCallsSkipped  = 0.0  # reset
                
                print(f"\n\nAccepted new states at {datetime.fromtimestamp(newStates.time)}\n")             # print(f"all new states: {[state.callsign for state in newStates.states]}")
                
                filteredNewStates = self.filter.filterStates(newStates.states)
                self.updateWindows(filteredNewStates)
                await asyncio.sleep(self.apiCallDelay) # wait for at least 10 seconds so not ratelimited by OpenSkyApi
  
    async def deadReckonLoop(self, dt:float=1.0) -> None:
        "Move windows in direction of true track with correct velocity every dt seconds"
        while True:
            t0 = time.monotonic()
            await asyncio.sleep(dt)
            dt = time.monotonic() - t0 # actual elapsed time
            for icao24, window in self.windows.items():
                if windowIsOpen(icao24):
                    window.deadReckonPosition(dt)
        
    async def runTracker(self) -> None:
        await asyncio.gather(self.fetchStatesLoop(), self.deadReckonLoop())






    

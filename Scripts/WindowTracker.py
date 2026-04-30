
from opensky_api import OpenSkyApi, StateVector, OpenSkyStates

# Core Python imports
import time
import json
import asyncio
from datetime import datetime
from dataclasses import dataclass, fields

# Custom imports
from Mover import Mover
from CustomQtWindow import MainWindow
from HandlingOpenSkyStates import fetchStatesInBbox
from Utils.Helpers import windowIsOpen



@dataclass
class WindowTrackerConfig:
    api: OpenSkyApi
    bboxAtLocation:tuple
    mover:Mover
    apiCallDelay:float = 10
    maxWindows:int = 3
    screenName:str|None = None
    minVelocity:float = 0
    departureAirport: str = ""
    arrivalAirport: str = ""
    originCountry: str = ""
    callsign: str = ""
    airline: str = ""
    icao24: str = ""
    
    @classmethod
    def loadSettings(cls, api, bboxAtLocation, mover, optionalSettingsPath:str|None = None):
        optionalSettings = {}
        validKeys = {field.name for field in fields(cls)}
        
        if optionalSettingsPath:
            with open(optionalSettingsPath) as f:
                groupedSettings = json.load(f)
    
            for group in groupedSettings.values():      # Flatten all groups into one dict, groups are merely for userfriendliness
                optionalSettings.update(group)
                
        filteredSettings = {key: value for key,value in optionalSettings.items() if key in validKeys}
        return cls(api, bboxAtLocation, mover, **filteredSettings)          


class WindowTracker():
    # def __init__(self, api:OpenSkyApi, bboxAtLocation:tuple, mover:Mover, apiCallDelay:float=10, maxWindows:int=3, screenName:str|None=None):
    def __init__(self, config:WindowTrackerConfig):
        self.config = config
        self.api            = config.api
        self.bboxAtLocation = config.bboxAtLocation
        self.mover          = config.mover
        self.maxWindows     = config.maxWindows
        self.screenName     = config.screenName
        self.apiCallDelay   = config.apiCallDelay
        self.minVelocity    = config.minVelocity
        
        self.windows:dict[str, MainWindow] = {}
        self.numApiCallsSkipped = 0.0
        self.newestApiUpdateTime = 0.0

    async def spawnWindow(self, state:StateVector) -> None:
        """Use spawns a window titled f\"qtApp_{state.icao24}\", also stores the new window in the windows dict with icao24 as key"""
        icao24 = state.icao24
        
        window = MainWindow(self.bboxAtLocation, state, self.mover, showOnScreenName = self.screenName)
        window.show()  # triggers QMainWindow.showEvent() 
        self.windows[icao24] = window
        print(f"Now tracking {state.callsign}")
        await asyncio.sleep(0.5)

    async def updateWindows(self, newStates:list[StateVector]) -> None:
        """Spawn, update, or close windows based on current aircraft states."""
        newIcaos = {state.icao24 for state in newStates}

        for state in newStates:
            if state.icao24 in self.windows and windowIsOpen(state.icao24):
                self.windows[state.icao24].updateState(state)
            elif len(self.windows) < self.maxWindows:
                await self.spawnWindow(state)

        for icao24 in list(self.windows.keys()):
            if icao24 not in newIcaos:
                self.windows[icao24].close()
                print(f"Stopped tracking {icao24}")
                del self.windows[icao24]

    async def fetchLocationsLoop(self) -> None: 
        """keep track of icao24 codes, spawn one window per code in bbox, close window if aircraft flies out of bbox"""
        
        assert self.apiCallDelay >= 10.0, "Please select an apiCallDelay of at least 10 seconds."
        
        while True:
            await asyncio.sleep(self.apiCallDelay) # wait for at least 10 seconds so not ratelimited by OpenSkyApi
            
            newStates:OpenSkyStates|None = fetchStatesInBbox(self.api, self.bboxAtLocation)  
            
            if not newStates or not newStates.states:
                print(f"New states are empty, continuing\n")
                self.numApiCallsSkipped += 1
                continue    # skip to next api call, else process exits.
            
            if newStates.time < self.newestApiUpdateTime: 
                print(f"New states older than previous, continuing\n")
                self.numApiCallsSkipped += 1
                continue    # skip if new timestamp older than previous timestamp
            
            if newStates.time - self.newestApiUpdateTime <= 0.8*(self.numApiCallsSkipped + 1)*self.apiCallDelay: # TODO: this filter shouldn't apply to new aircraft appearing in bbox
                print(f"New api call spacing too short, continuing\n")
                self.numApiCallsSkipped += 1
                continue    # skip if difference between timestamps is less than the elapsed real time
            
            self.newestApiUpdateTime = newStates.time
            self.numApiCallsSkipped  = 0.0  # reset
            
            print(f"New states at {datetime.fromtimestamp(newStates.time)}\n")
            filteredNewStates = self.filterStates(newStates.states)
            await self.updateWindows(filteredNewStates)
  
    async def deadReckonLoop(self, dt:float=1.0) ->None:
        "Move windows in direction of true track with correct velocity every dt seconds"
        while True:
            t0 = time.monotonic()
            await asyncio.sleep(dt)
            dt = time.monotonic() - t0 # actual elapsed time
            for icao24, window in self.windows.items():
                if windowIsOpen(icao24):
                    window.deadReckonPosition(dt)
     
    def filterStatesMinVelocity(self, states:list[StateVector], debugPrintFlag:bool = False):
        filteredStates = []
        for state in states:
            if state.velocity is not None:
                
                if not state.velocity >= self.minVelocity:
                    if state.on_ground == True:
                        if debugPrintFlag: print(f"Filtered Callsign {state.callsign} because velocity on ground too slow")
                    
                else:
                    if debugPrintFlag: print(f"Callsign {state.callsign} passed velocity filter")
                    filteredStates.append(state)
                
        return filteredStates
    
    def filterStates(self, states:list[StateVector]):
        
        if self.config.minVelocity:
            print(f"Filtering for minVelocity: {self.config.minVelocity}")
            states = self.filterStatesMinVelocity(states)
            
        if self.config.departureAirport:
            pass
        if self.config.arrivalAirport:
            pass
        if self.config.originCountry:
            pass
        
        if self.config.callsign:
            print(f"Filtering for callsign {self.config.callsign}")
            states = [state for state in states if state.callsign == self.config.callsign]
            
        if self.config.airline:
            print(f"Filtering for airline: {self.config.airline}")
            states = [state for state in states if state.callsign is not None and state.callsign.startswith(self.config.airline)]
            
        if self.config.icao24:
            print(f"Filtering for icao24: {self.config.icao24}")
            states = [state for state in states if state.icao24 == self.config.icao24]
        
        if self.config.maxWindows:
            print(f"Restricting number of windows to: {self.config.maxWindows}")
            states = states[:self.config.maxWindows]
        return states    
        
    async def runTracker(self, initialStates:list[StateVector]) -> None:
        # spawn all windows for planes in bbox and matching filter criteria
        filteredStates = self.filterStates(initialStates)
        for state in filteredStates:
            await self.spawnWindow(state)
            
        # update the location of the windows / check for new/removed planes / check if windows were closed manually.        
        await asyncio.gather(self.fetchLocationsLoop(), self.deadReckonLoop())






    

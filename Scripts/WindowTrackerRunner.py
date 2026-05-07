
from opensky_api import OpenSkyStates

#Core Python imports
import time
import asyncio
from datetime import datetime


# Custom imports
from WindowTracker import WindowTracker
from WindowTrackerConfig import WindowTrackerConfig
from HandlingOpenSkyStates import fetchStatesInBbox


class WindowTrackerRunner():
    def __init__(self, tracker: WindowTracker, config: WindowTrackerConfig):
        self.tracker = tracker
        
        self.api            = config.api
        self.bboxAtLocation = config.bboxAtLocation
        self.apiCallDelay   = config.apiConfig.apiCallDelay
        self.updateInterval = config.visuals.updateInterval
        
        self.newestStateTimestamp = 0.0
        self.numApiCallsSkipped   = 0.0
        
    async def waitWithDeadReckoning(self, duration:float) -> None:
        """ Pass apiCallDelay (despite self.apiCallDelay also being available here) to make it clear how long this function takes from where it's called."""
        
        dt = self.updateInterval
        deadline = time.monotonic() + duration
        
        while time.monotonic() < deadline:
            t0 = time.monotonic()
            await asyncio.sleep(dt)
            
            actualTimePassed = time.monotonic() - t0
            self.tracker.deadReckonWindows(actualTimePassed)

    async def fetchStatesLoop(self):
        
        assert self.apiCallDelay >= 10.0, "apiCallDelay must be at least 10 seconds."
        
        while True:
                
                newStates:OpenSkyStates|None = fetchStatesInBbox(self.api, self.bboxAtLocation)  
                
                # skip to next api call if newStates empty.
                if not newStates or not newStates.states:
                    print(f"New states are empty, continuing\n")
                    self.numApiCallsSkipped += 1
                    
                    await self.waitWithDeadReckoning(self.apiCallDelay)
                    continue    
                
                # skip if new timestamp older than previous timestamp
                if newStates.time < self.newestStateTimestamp: 
                    print(f"New states older than previous, continuing\n")
                    self.numApiCallsSkipped += 1
                    
                    await self.waitWithDeadReckoning(self.apiCallDelay)
                    continue    
                
                # skip if difference between timestamps is less than the elapsed real time. Factor 0.9 to accept decent newStates
                if newStates.time - self.newestStateTimestamp <= 0.9*(self.numApiCallsSkipped + 1)*self.apiCallDelay:
                    
                    # If there are previously untracked states in the newest api call result, add those to tracked states. Even if the spacing is too short.
                    untrackedStates = self.tracker.filter.extractUntrackedStates(self.tracker.windows, newStates.states)
                    filteredUntrackedStates = self.tracker.filter.filterStates(untrackedStates)
                    self.tracker.updateWindows(filteredUntrackedStates, delete = False)

                    print(f"New api call spacing too short, continuing\n")
                    self.numApiCallsSkipped += 1
                    
                    await self.waitWithDeadReckoning(self.apiCallDelay)
                    continue    
                
                self.newestStateTimestamp = newStates.time
                self.numApiCallsSkipped  = 0.0  # reset
                
                print(f"\n\nAccepted {len(newStates.states)} new states at {datetime.fromtimestamp(int(time.time()))} with timestamp: {datetime.fromtimestamp(newStates.time)}\n")             # print(f"all new states: {[state.callsign for state in newStates.states]}")
                
                filteredNewStates = self.tracker.filter.filterStates(newStates.states)
                self.tracker.updateWindows(filteredNewStates)
                
                await self.waitWithDeadReckoning(self.apiCallDelay)

    async def run(self) -> None:
        await self.fetchStatesLoop()


    

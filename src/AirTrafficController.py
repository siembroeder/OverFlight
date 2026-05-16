
from opensky_api import OpenSkyStates

#Core Python imports
import time
import asyncio
import logging
logger = logging.getLogger(__name__)
from datetime import datetime


# Custom imports
from WindowTracker import WindowTracker
from utils.OpenSkyUtils import fetchStatesInBbox


class AirTrafficController():
    """
    Controls WindowTracker.
    Responsible for fetching aircraft states and for waiting in between api calls for apiCallDelay seconds. 
    Must be longer than 10 seconds to not be ratelimited by the openskyapi if you're using a free subscription 
    """
    def __init__(self, tracker: WindowTracker):
        self.tracker = tracker
        
        self.bboxAtLocation = self.tracker.settings.bboxAtLocation
        self.apiCallDelay   = self.tracker.settings.api.apiCallDelay
        self.updateInterval = self.tracker.settings.visuals.updateInterval
        
        self.newestStateTimestamp = 0.0
        self.numApiCallsSkipped   = 0.0
        
    async def waitWithDeadReckoning(self, delayTime:float) -> None:
        """ 
        Async loop waiting for the next api call while applying dead reckoning to tracked windows.
        
        Pass apiCallDelay explicitly (despite self.apiCallDelay also being available here) to make it clear how long this function takes from where it's called.
        """
        
        dt = self.tracker.settings.visuals.updateInterval
        deadline = time.monotonic() + delayTime
        
        while time.monotonic() < deadline:
            await asyncio.sleep(dt)
            self.tracker.deadReckonWindows()

    async def fetchStatesLoop(self):
        """
        Main asynchronous loop that fetches aircraft states, applies filtering, rate-limits API usage, and updates tracked windows.
        """
        
        assert self.apiCallDelay >= 10.0, "apiCallDelay must be at least 10 seconds."
        
        while True:
            
                # update settings if changed during runtime
                self.tracker.checkNewSettings()
            
                # fetch new states, ratelimiting is handled in .waitWithDeadReckoning
                newStates:OpenSkyStates|None = fetchStatesInBbox(self.tracker.settings.openSkyApi, self.bboxAtLocation)  

                # skip to next api call if newStates empty.
                if (newStates is None) or (newStates.states is None):
                    logger.debug("New states are empty, continuing\n")
                    self.numApiCallsSkipped += 1
                    
                    await self.waitWithDeadReckoning(self.apiCallDelay)
                    continue    
                
                # skip if new timestamp older than previous timestamp
                if newStates.time < self.newestStateTimestamp: 
                    logger.debug("New states older than previous, continuing\n")
                    self.numApiCallsSkipped += 1
                    
                    await self.waitWithDeadReckoning(self.apiCallDelay)
                    continue    
                
                # skip if difference between timestamps is less than the elapsed real time. Factor 0.9 to accept decent newStates
                if newStates.time - self.newestStateTimestamp <= 0.9*(self.numApiCallsSkipped + 1)*self.apiCallDelay:
                    
                    # If there are previously untracked states in the newest api call result, add those to tracked states. Even if the spacing is too short.
                    untrackedStates = self.tracker.filter.extractUntrackedStates(self.tracker.windows, newStates.states)
                    filteredUntrackedStates = self.tracker.filter.filterStates(untrackedStates)
                    self.tracker.updateWindows(filteredUntrackedStates, delete = False)

                    logger.debug("New api call spacing too short, continuing\n")
                    self.numApiCallsSkipped += 1
                    
                    await self.waitWithDeadReckoning(self.apiCallDelay)
                    continue    
                
                self.newestStateTimestamp = newStates.time
                self.numApiCallsSkipped   = 0.0  # reset
                
                logger.info(f"\n\nAccepted {len(newStates.states)} new states at {datetime.fromtimestamp(int(time.time()))} with timestamp: {datetime.fromtimestamp(newStates.time)}\n")
                
                filteredNewStates = self.tracker.filter.filterStates(newStates.states)
                self.tracker.updateWindows(filteredNewStates)
                                
                await self.waitWithDeadReckoning(self.apiCallDelay)

    async def run(self) -> None:
        await self.fetchStatesLoop()


# # use these to test / if no internet is available

# sVector = [["icao24",
#             "KLM123",
#             "NL",
#             123456789,
#             987654321,
#             52.3,
#             4.89,
#             10000,
#             False,
#             300,
#             270.4,
#             None,
#             None,
#             11000,
#             "7700",
#             False,
#             0,
#             0]]

# NEW_STATES = OpenSkyStates({"time": time.time(), "states": sVector})


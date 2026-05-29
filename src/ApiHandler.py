import time
import asyncio
import logging

from Settings import Settings
from StateFilter import StateFilter
logger = logging.getLogger(__name__)

from opensky_api import OpenSkyStates
from utils.OpenSkyUtils import fetchStatesInBbox


class ApiHandler():
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        self.bboxAtLocation = self.settings.bboxAtLocation
        self.apiCallDelay   = self.settings.api.apiCallDelay

        self.newestStateTimestamp = 0.0
        self.numApiCallsSkipped   = 0.0

    def fetchStates(self, trackerWindows, filter:StateFilter) -> tuple[OpenSkyStates | None, list]:
        """
        Fetches and validates new states.
        Returns (accepted_states, untracked_filtered_states).
        accepted_states is None if this call should be skipped.
        untracked_filtered_states is non-empty only on too-frequent calls.
        """
        newStates: OpenSkyStates | None = fetchStatesInBbox(self.settings.openSkyApi, self.bboxAtLocation)

        # skip to next api call if newStates empty.
        if (newStates is None) or (newStates.states is None):
            logger.debug("New states are empty, continuing\n")
            self.numApiCallsSkipped += 1
            return None, []
        
        # skip if new timestamp older than previous timestamp
        if newStates.time < self.newestStateTimestamp:
            logger.debug("New states older than previous, continuing\n")
            self.numApiCallsSkipped += 1
            return None, []
        
        # skip if difference between timestamps is less than the elapsed real time. Factor 0.9 to accept decent newStates
        if newStates.time - self.newestStateTimestamp <= 0.9 * (self.numApiCallsSkipped + 1) * self.apiCallDelay:
            logger.debug("New api call spacing too short, continuing\n")
            self.numApiCallsSkipped += 1
            untracked = filter.extractUntrackedStates(trackerWindows, newStates.states)
            return None, filter.filterStates(untracked)

        self.newestStateTimestamp = newStates.time
        self.numApiCallsSkipped   = 0.0
        return newStates, []

    async def fetchStatesLoop(self, queue: asyncio.Queue, trackerWindows, filterObj) -> None:
        """Fetches states on a fixed interval and puts results onto the queue."""
        assert self.apiCallDelay >= 5.0, "apiCallDelay must be at least 5.0 seconds."

        while True:
            result = self.fetchStates(trackerWindows, filterObj)
            await queue.put(result)
            await asyncio.sleep(self.apiCallDelay)
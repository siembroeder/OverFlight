import time
import asyncio
import logging

from settings import Settings
from state_filter import StateFilter
logger = logging.getLogger(__name__)

from opensky_api import OpenSkyStates, StateVector
from utils.open_sky_utils import fetchStatesInBbox


class ApiHandler():
    def __init__(self, settings: Settings) -> None:
        self.settings = settings

        self.bbox_at_location = self.settings.bbox_at_location
        self.api_call_delay   = self.settings.api.api_call_delay

        self.last_api_call_timestamp = 0.0
        self.newest_state_timestamp = 0.0
        self.num_api_calls_skipped   = 0.0

    def fetch_states(self, tracker_windows, filter:StateFilter) -> tuple[OpenSkyStates | None, list[StateVector]]:
        """
        Fetches and validates new states.
        Returns (accepted_states, untracked_filtered_states).
        accepted_states is None if this call should be skipped.
        untracked_filtered_states is non-empty only on too-frequent calls.
        """
        new_states: OpenSkyStates | None = fetchStatesInBbox(self.settings.open_sky_api, self.bbox_at_location)
        self.last_api_call_timestamp = time.monotonic()

        # skip to next api call if newStates empty.
        if (new_states is None) or (new_states.states is None):
            logger.debug("New states are empty, continuing\n")
            self.num_api_calls_skipped += 1
            return None, []
        
        # skip if new timestamp older than previous timestamp
        if new_states.time < self.newest_state_timestamp:
            logger.debug("New states older than previous, continuing\n")
            self.num_api_calls_skipped += 1
            return None, []
        
        # skip if difference between timestamps is less than the elapsed real time. Factor 0.9 to accept decent newStates
        if new_states.time - self.newest_state_timestamp <= 0.9 * (self.num_api_calls_skipped + 1) * self.api_call_delay:
            logger.debug("New api call spacing too short, continuing\n")
            self.num_api_calls_skipped += 1
            untracked = filter.extract_untracked_states(tracker_windows, new_states.states)
            return None, untracked

        self.newest_state_timestamp = new_states.time
        self.num_api_calls_skipped   = 0.0
        return new_states, []

    async def fetch_states_loop(self, queue: asyncio.Queue, tracker_windows, filter_obj) -> None:
        """Fetches states on a fixed interval and puts results onto the queue."""
        assert self.api_call_delay >= 5.0, "apiCallDelay must be at least 5.0 seconds."
        while True:
            result = self.fetch_states(tracker_windows, filter_obj)
            await queue.put(result)

            now = time.monotonic()
            next_allowed = self.last_api_call_timestamp + self.api_call_delay
            wait = max(0.0, next_allowed - now)
            await asyncio.sleep(wait)
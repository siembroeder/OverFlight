import time
import asyncio
import logging
from dataclasses import fields
from datetime import datetime

from settings import Settings
from state_filter import StateFilter
logger = logging.getLogger(__name__)

from opensky_api import OpenSkyStates, StateVector
from utils.open_sky_utils import fetch_states_in_bbox
from utils.icao8643_utils import Icao8643Entry
from utils.aircraft_record import AircraftRecord
from opensky_api import StateVector


class ApiHandler():
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.build_filter()
        for f in fields(settings.tracking): # if any field in settings.tracking changes, rebuild the filter completely
            settings.on_change(f.name, lambda _: self.build_filter())

        # load dicts of aircraft data into memory
        self.icao24_to_typecode:dict[str, str]          = Icao8643Entry.load_icao24_to_typecode()
        self.typecode_to_entry:dict[str, Icao8643Entry] = Icao8643Entry.load_typecodes_to_icao8643_entry()

        self.bbox_at_location = self.settings.bbox_at_location
        self.api_call_delay   = self.settings.api.api_call_delay

        self.last_api_call_timestamp = 0.0
        self.newest_state_timestamp = 0.0
        self.num_api_calls_skipped   = 0.0

    def fetch_states(self, tracker_windows) -> tuple[OpenSkyStates | None, list[StateVector]]:
        """
        Fetches and validates new states.
        Returns (accepted_states, untracked_filtered_states).
        accepted_states is None if this call should be skipped.
        untracked_filtered_states is non-empty only on too-frequent calls.
        """
        new_states: OpenSkyStates | None = fetch_states_in_bbox(self.settings.open_sky_api, self.bbox_at_location)
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
            untracked = self.filter.extract_untracked_states(tracker_windows, new_states.states)
            return None, untracked

        self.newest_state_timestamp = new_states.time
        self.num_api_calls_skipped   = 0.0
        return new_states, []

    async def fetch_states_loop(self, queue: asyncio.Queue, tracker_windows) -> None:
        """Fetches states on a fixed interval and puts results onto the queue."""
        assert self.api_call_delay >= 5.0, "apiCallDelay must be at least 5.0 seconds."
        while True:
            accepted, untracked = self.fetch_states(tracker_windows)
            filtered_accepted_aircraft, filtered_untracked_aircraft = None, None
            if accepted:
                logger.info(f"\n\nAccepted {len(accepted.states)} new states at "
                            f"{datetime.fromtimestamp(int(time.time()))} with timestamp: "
                            f"{datetime.fromtimestamp(accepted.time)}\n")
                
                accepted_aircraft = self.to_aircraft_records(accepted.states)
                filtered_accepted_aircraft = self.filter.filter_aircraft(accepted_aircraft)
                logger.debug(f"After filtering {len(filtered_accepted_aircraft)} remain.\n")
            if untracked:
                untracked_aircraft = self.to_aircraft_records(untracked)
                filtered_untracked_aircraft = self.filter.filter_aircraft(untracked_aircraft)
            await queue.put((filtered_accepted_aircraft, filtered_untracked_aircraft))

            now = time.monotonic()
            next_allowed = self.last_api_call_timestamp + self.api_call_delay
            wait = max(0.0, next_allowed - now)
            await asyncio.sleep(wait)

    def to_aircraft_records(self, states:list[StateVector], fallback_typecode:str = "C172") -> list[AircraftRecord]:

        records = []
        for state in states:
            typecode = self.icao24_to_typecode.get(state.icao24) or fallback_typecode
            entry    = self.typecode_to_entry[typecode]
            records.append(AircraftRecord(state=state, entry=entry))

        return records

    def build_filter(self):
        self.filter = StateFilter(self.settings.tracking, self.settings.open_sky_api, self.settings.setup.max_windows, self.settings.bbox_at_location)
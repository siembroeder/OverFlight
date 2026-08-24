import time
import asyncio
import logging
from dataclasses import fields
from datetime import datetime

from state_filter import StateFilter
logger = logging.getLogger(__name__)

from opensky_api import OpenSkyStates, StateVector
from utils.open_sky_utils import get_states_in_bbox_and_credits # fetch_states_in_bbox,
from utils.icao8643_utils import Icao8643Entry
from aircraft_record import AircraftRecord
from opensky_api import StateVector
from settings import app_settings

class ApiHandler():
    def __init__(self) -> None:
        self.build_filter()
        for f in fields(app_settings.tracking): # if any field in settings.tracking changes, rebuild the filter completely
            app_settings.on_change(f.name, lambda _: self.build_filter())
        app_settings.on_change("max_windows", lambda _ : self.build_filter())

        # load dicts of aircraft data into memory
        self.icao24_to_typecode:dict[str, str]          = Icao8643Entry.load_icao24_to_typecode()
        self.typecode_to_entry:dict[str, Icao8643Entry] = Icao8643Entry.load_typecodes_to_icao8643_entry()

        self.last_api_call_timestamp = 0.0
        self.newest_state_timestamp = 0.0
        self.num_api_calls_skipped   = 0.0

    def fetch_states(self) -> tuple[OpenSkyStates | None, bool]:
        """
        Fetches and validates new states. Returns new states and whether they are fresh.

        :return: The new states and whether they are fresh
        :rtype: tuple[OpenSkyStates | None, bool]
        """
        new_states, remaining_credits = get_states_in_bbox_and_credits(app_settings.open_sky_api, app_settings.bbox_at_location)
        # new_states: OpenSkyStates | None = fetch_states_in_bbox(app_settings.open_sky_api, self.bbox_at_location)
        self.last_api_call_timestamp = time.monotonic()

        # skip to next api call if newStates empty.
        if (new_states is None) or (new_states.states is None):
            logger.debug(f"New states are empty, remaining credits: {remaining_credits}, continuing\n")
            self.num_api_calls_skipped += 1
            return None, False
        
        # skip if new timestamp older than previous timestamp, if bbox_changed all widgets are closed -> accept the first new states
        if new_states.time < self.newest_state_timestamp and not app_settings.bbox_updated:
            logger.debug("New states older than previous, continuing\n")
            self.num_api_calls_skipped += 1
            return None, False
        
        # difference between timestamps is less than the elapsed real time. Factor 0.9 to accept decent newStates
        fresh = new_states.time - self.newest_state_timestamp > 0.8 * (self.num_api_calls_skipped + 1) * app_settings.api.api_call_delay
        
        if fresh:
            self.newest_state_timestamp = new_states.time
            self.num_api_calls_skipped = 0.0
        else:
            self.num_api_calls_skipped += 1

        if app_settings.bbox_updated:
            app_settings.bbox_updated = False 

        return new_states, fresh

    async def fetch_states_loop(self, queue: asyncio.Queue) -> None:
        """Fetches states on a fixed interval and puts filtered results onto the queue."""
        assert app_settings.api.api_call_delay >= 5.0, "apiCallDelay must be at least 5.0 seconds."
        while True:
            new_states, fresh = self.fetch_states()
            filtered_aircrafts = None
            if new_states:
                logger.info(f"\tAccepted {len(new_states.states)} new states at "
                            f"{datetime.fromtimestamp(int(time.time()))} with timestamp: "
                            f"{datetime.fromtimestamp(new_states.time)}")
                
                aircrafts = self.to_aircraft_records(new_states.states)
                filtered_aircrafts = self.filter.filter_aircraft(aircrafts)
                logger.debug(f"After filtering {len(filtered_aircrafts)} remain.")
            await queue.put((filtered_aircrafts, fresh))

            now = time.monotonic()
            next_allowed = self.last_api_call_timestamp + app_settings.api.api_call_delay
            wait = max(0.0, next_allowed - now)
            await asyncio.sleep(wait)

    def to_aircraft_records(self, states:list[StateVector], fallback_typecode:str = "C172") -> list[AircraftRecord]:

        records = []
        for state in states:
            typecode = None
            try:
                typecode = self.icao24_to_typecode.get(state.icao24) or fallback_typecode
                entry    = self.typecode_to_entry[typecode]
                records.append(AircraftRecord(state=state, entry=entry))
            except:
                logger.debug(f"Skipping typecode: {typecode} state to record because of error.")
                continue

        return records

    def build_filter(self):
        self.filter = StateFilter(app_settings.tracking, app_settings.open_sky_api, app_settings.setup.max_windows, app_settings.bbox_at_location)
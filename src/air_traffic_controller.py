import time
import asyncio
import logging

from settings import Settings
logger = logging.getLogger(__name__)
from datetime import datetime

from api_handler import ApiHandler
from window_tracker import WindowTracker
from utils.icao8643_utils import Icao8643Entry
from utils.aircraft_record import AircraftRecord
from opensky_api import StateVector


class AirTrafficController():
    def __init__(self, settings:Settings, api_handler: ApiHandler, tracker: WindowTracker):
        self.settings   = settings
        self.api_handler = api_handler
        self.tracker    = tracker
        
        # load dicts of aircraft data into memory
        self.icao24_to_typecode:dict[str, str]          = Icao8643Entry.load_icao24_to_typecode()
        self.typecode_to_entry:dict[str, Icao8643Entry] = Icao8643Entry.load_typecodes_to_icao8643_entry()

    async def _dead_reckon_loop(self) -> None:
        """Continuously applies dead reckoning at the visual update interval."""
        dt = self.tracker.settings.visuals.update_interval
        while True:
            await asyncio.sleep(dt)
            self.tracker.dead_reckon_windows()

    async def _consume_states_loop(self) -> None:
        """Consumes fetched states from the queue and updates windows."""
        queue = asyncio.Queue(maxsize=1)

        asyncio.create_task(
            self.api_handler.fetch_states_loop(
                queue,
                self.tracker.windows,
                self.tracker.filter,
            )
        )

        while True:
            self.tracker.check_new_settings()
            accepted, untracked = await queue.get()

            if untracked:
                untracked_aircraft = self.to_aircraft_records(untracked)
                filtered_untracked_aircraft = self.tracker.filter.filter_aircraft(untracked_aircraft)
                self.tracker.update_windows(filtered_untracked_aircraft, delete=False)

            if accepted is None:
                continue

            logger.info(f"\n\nAccepted {len(accepted.states)} new states at "
                        f"{datetime.fromtimestamp(int(time.time()))} with timestamp: "
                        f"{datetime.fromtimestamp(accepted.time)}\n")

            accepted_aircraft = self.to_aircraft_records(accepted.states)
            filtered_aircraft = self.tracker.filter.filter_aircraft(accepted_aircraft)
            logger.debug(f"After filtering {len(filtered_aircraft)} remain.\n")
            self.tracker.update_windows(filtered_aircraft)

    async def run(self) -> None:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._dead_reckon_loop())
            tg.create_task(self._consume_states_loop())
        logger.critical("Main loop stopped.\n")

    def to_aircraft_records(self, states:list[StateVector], fallback_typecode:str = "C172") -> list[AircraftRecord]:

        records = []
        for state in states:
            typecode = self.icao24_to_typecode.get(state.icao24) or fallback_typecode
            entry    = self.typecode_to_entry[typecode]
            records.append(AircraftRecord(state=state, entry=entry))

        return records

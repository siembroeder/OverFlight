import time
import asyncio
import logging

from Settings import Settings
logger = logging.getLogger(__name__)
from datetime import datetime

from ApiHandler import ApiHandler
from WindowTracker import WindowTracker
from utils.Icao8643Utils import Icao8643Entry
from utils.AircraftRecord import AircraftRecord
from opensky_api import StateVector


class AirTrafficController():
    def __init__(self, settings:Settings, apiHandler: ApiHandler, tracker: WindowTracker):
        self.settings   = settings
        self.apiHandler = apiHandler
        self.tracker    = tracker
        
        # load dicts of aircraft data into memory
        self.icao24ToTypecode:dict[str, str]          = Icao8643Entry.loadIcao24ToTypecode()
        self.typecodeToEntry:dict[str, Icao8643Entry] = Icao8643Entry.loadTypecodesToIcao8643Entry()

    async def _deadReckonLoop(self) -> None:
        """Continuously applies dead reckoning at the visual update interval."""
        dt = self.tracker.settings.visuals.updateInterval
        while True:
            await asyncio.sleep(dt)
            self.tracker.deadReckonWindows()

    async def _consumeStatesLoop(self) -> None:
        """Consumes fetched states from the queue and updates windows."""
        queue = asyncio.Queue(maxsize=1)

        asyncio.create_task(
            self.apiHandler.fetchStatesLoop(
                queue,
                self.tracker.windows,
                self.tracker.filter,
            )
        )

        while True:
            self.tracker.checkNewSettings()
            accepted, untracked = await queue.get()

            if untracked:
                untrackedAircraft = self.toAircraftRecords(untracked)
                self.tracker.updateWindows(untrackedAircraft, delete=False)

            if accepted is None:
                continue

            logger.info(f"\n\nAccepted {len(accepted.states)} new states at "
                        f"{datetime.fromtimestamp(int(time.time()))} with timestamp: "
                        f"{datetime.fromtimestamp(accepted.time)}\n")

            acceptedAircraft = self.toAircraftRecords(accepted.states)
            filteredAircraft = self.tracker.filter.filterAircraft(acceptedAircraft)
            logger.debug(f"After filtering {len(filteredAircraft)} remain.\n")
            self.tracker.updateWindows(filteredAircraft)

    async def run(self) -> None:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._deadReckonLoop())
            tg.create_task(self._consumeStatesLoop())
        logger.critical("Main loop stopped.\n")

    def toAircraftRecords(self, states:list[StateVector], fallbackTypecode:str = "C172") -> list[AircraftRecord]:

        records = []
        for state in states:
            typecode = self.icao24ToTypecode.get(state.icao24) or fallbackTypecode
            entry    = self.typecodeToEntry[typecode]
            records.append(AircraftRecord(state=state, entry=entry))

        return records

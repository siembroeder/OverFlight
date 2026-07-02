import time
import asyncio
import logging
logger = logging.getLogger(__name__)

from utils.aircraft_record import AircraftRecord
from settings import app_settings
from api_handler import ApiHandler
from aircraft_tracker import AircraftTracker


class AirTrafficController():
    def __init__(self, api_handler: ApiHandler, tracker: AircraftTracker):
        self.api_handler = api_handler
        self.tracker = tracker

    async def _dead_reckon_loop(self) -> None:
        """Continuously applies dead reckoning at the visual update interval."""
        dt = app_settings.visuals.update_interval
        while True:
            await asyncio.sleep(dt)
            self.tracker.dead_reckon_windows()

    async def _consume_states_loop(self) -> None:
        """Consumes fetched states from the queue and updates windows."""
        queue: asyncio.Queue[tuple[list[AircraftRecord] | None, bool]] = asyncio.Queue(maxsize=1)

        asyncio.create_task(
            self.api_handler.fetch_states_loop(queue)
        )

        while True:
            aircrafts, fresh = await queue.get()

            if aircrafts:
                self.tracker.update_aircrafts(aircrafts, fresh)

    async def run(self) -> None:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._dead_reckon_loop())
            tg.create_task(self._consume_states_loop())
        logger.critical("Main loop stopped.\n")

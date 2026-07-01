import time
import asyncio
import logging

from settings import Settings
logger = logging.getLogger(__name__)

from api_handler import ApiHandler
from window_tracker import WindowTracker


class AirTrafficController():
    def __init__(self, settings:Settings, api_handler: ApiHandler, tracker: WindowTracker):
        self.settings   = settings
        self.api_handler = api_handler
        self.tracker    = tracker

    async def _dead_reckon_loop(self) -> None:
        """Continuously applies dead reckoning at the visual update interval."""
        dt = self.settings.visuals.update_interval
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
            )
        )

        while True:
            self.tracker.check_new_settings()
            accepted, untracked = await queue.get()

            if untracked:
                self.tracker.update_windows(untracked, delete=False)

            if accepted:
                self.tracker.update_windows(accepted)

    async def run(self) -> None:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._dead_reckon_loop())
            tg.create_task(self._consume_states_loop())
        logger.critical("Main loop stopped.\n")

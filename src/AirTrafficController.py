import time
import asyncio
import logging

from Settings import Settings
logger = logging.getLogger(__name__)
from datetime import datetime

from ApiHandler import ApiHandler
from WindowTracker import WindowTracker


class AirTrafficController():
    def __init__(self, settings:Settings, apiHandler: ApiHandler, tracker: WindowTracker):
        self.settings   = settings
        self.apiHandler = apiHandler
        self.tracker    = tracker

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
                self.tracker.updateWindows(untracked, delete=False)

            if accepted is None:
                continue

            logger.info(f"\n\nAccepted {len(accepted.states)} new states at "
                        f"{datetime.fromtimestamp(int(time.time()))} with timestamp: "
                        f"{datetime.fromtimestamp(accepted.time)}\n")

            filtered = self.tracker.filter.filterStates(accepted.states)
            logger.debug(f"After filtering {len(filtered)} remain.\n")
            self.tracker.updateWindows(filtered)

    async def run(self) -> None:
        async with asyncio.TaskGroup() as tg:
            tg.create_task(self._deadReckonLoop())
            tg.create_task(self._consumeStatesLoop())
        logger.critical("Main loop stopped.\n")

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


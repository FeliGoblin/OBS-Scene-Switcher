import asyncio
import logging

from actions import Action
from alerts import Alert
from data import Data
from helpers import Helpers
from transitions import Transition
from websocket import WebSocket

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger("Manager")


class Overlay_Manager:
    def __init__(self):
        self.data = Data()
        self.helper = Helpers(self.data)
        self.action = Action(self.helper, self.data)
        self.transition = Transition(self.action)
        self.alert = Alert(self.action)
        self.websocket = WebSocket(self.helper, self.action, self.transition, self.alert)

    async def setup(self):
        await self.websocket._trigger()
        self.alert.worker_task = asyncio.create_task(self.alert._worker())
        self.transition.worker_task = asyncio.create_task(self.transition._worker())


def main():
    overlay_manager = Overlay_Manager()
    loop = asyncio.new_event_loop()

    _LOGGER.info(
        "Starting event loop, scheduling OBS WebSocket and Queue setup..."
    )
    loop.call_soon(asyncio.create_task, overlay_manager.setup())
    try:
        loop.run_forever()
    finally:
        _LOGGER.info("Loop stopped. Cleaning up...")
        pending = asyncio.all_tasks(loop)
        for task in pending:
            task.cancel()
        loop.close()


if __name__ == "__main__":
    main()

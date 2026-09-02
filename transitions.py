import asyncio
import logging

from actions import Action
from const import HIDE, SHOW, Idle_Text

_LOGGER = logging.getLogger("Transitions")


class Transition:
    def __init__(self, action: Action):
        self.action = action
        self.queue = asyncio.Queue()
        self.worker_task: asyncio.Task | None = None

    async def _worker(self):
        while True:
            transition, event_data = await self.queue.get()
            try:
                await transition(event_data)
            except Exception:
                _LOGGER.exception("Transition playback failed")
            finally:
                self.queue.task_done()

    async def Starting_Soon(self, data: dict):
        await self.action.Show_Idle_Overlay(Idle_Text.STARTING_SOON, data.get("cam", False))

    async def Be_Right_Back(self, data: dict):
        await self.action.Show_Idle_Overlay(Idle_Text.BE_RIGHT_BACK, data.get("cam", False))

    async def Stream_Ending(self, data: dict):
        await self.action.Show_Idle_Overlay(Idle_Text.STREAM_ENDING, data.get("cam", False))

    async def Live(self, *args):
        await self.action.Live.Fullscreen_Cam(HIDE)
        await self.action.Hide_Idle_Overlay()

    async def Fullscreen_Cam(self, *args):
        await self.action.Live.Fullscreen_Cam(SHOW)
        await self.action.Hide_Idle_Overlay()

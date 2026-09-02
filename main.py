import asyncio
import logging

import simpleobsws

from actions import Action
from alerts import Alert
from const import OBS, OFF, ON
from data import Data
from helpers import Helpers
from secret import Secret
from transitions import Transition

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger("Manager")


class Overlay_Manager:
    def __init__(self):
        # Data
        self.data = Data()

        # OBS
        self.websocket: simpleobsws.WebSocketClient | None = None
        self.websocket_reconnect_task: asyncio.Task | None = None
        self.websocket_connected: bool = False

        self.helper = Helpers(self.data)
        self.action = Action(self.helper, self.data)
        self.transition = Transition(self.action)
        self.alert = Alert(self.action)

    async def setup(self):
        await self.trigger_websocket()
        self.alert.worker_task = asyncio.create_task(self.alert._worker())
        self.transition.worker_task = asyncio.create_task(self.transition._worker())

    async def trigger_websocket(self):
        if self.websocket:
            await self.config_websocket_status(OFF)
            return
        self.websocket_reconnect_task = asyncio.create_task(
            self.connect_obs_websocket()
        )

    async def config_websocket_status(self, toggle: bool) -> None:
        if not toggle:
            # if self.websocket and self.websocket.is_identified():
            if self.websocket:
                await self.websocket.disconnect()
            if self.websocket_reconnect_task:
                self.websocket_reconnect_task.cancel()
            self.websocket = None
            self.websocket_reconnect_task = None
        self.websocket_connected = toggle

    async def connect_obs_websocket(self) -> None:
        """Set up async OBS WebSocket client and get scene item IDs."""
        attempt = 0
        disconnected = False

        self.websocket = simpleobsws.WebSocketClient(
            url=Secret.OBS_WS_URL, password=Secret.OBS_WS_PWD
        )

        # Adding the WS session to the helper now that one is created.
        self.helper.websocket = self.websocket

        while True:
            if self.websocket_connected:
                if self.websocket and self.websocket.is_identified():
                    _LOGGER.debug("OBS WebSocket identified.")
                    await asyncio.sleep(OBS.DELAY)
                    continue
                _LOGGER.warning(
                    "OBS WebSocket disconnected, attempting reconnect %s...",
                    attempt + 1,
                )
                self.websocket_connected = False
                disconnected = True

            if attempt >= OBS.RETRIES:
                _LOGGER.warning("Connection failed. Stopping attempts.")
                await self.config_websocket_status(OFF)
                break
            attempt += 1

            _LOGGER.info("Attempting to connect to OBS WebSocket...")

            try:
                await self.websocket.connect()
                await self.websocket.wait_until_identified()

                _LOGGER.info("Connected to OBS!")
                attempt = 0
                disconnected = False
                await self.config_websocket_status(ON)

                # Register events to listen for.
                self.websocket.register_event_callback(
                    self.CustomEvent,
                    "CustomEvent",
                )

                await self.helper.get_obs_item_ids()
                await self.helper.get_obs_audio_inputs()

            except Exception:
                _LOGGER.exception("OBS connection failed")
                if not disconnected:
                    await self.config_websocket_status(OFF)
                    break
            else:
                await asyncio.sleep(OBS.DELAY)

    async def CustomEvent(self, eventData: dict[str, dict[str, str]]):
        """Got a CustomEvent through OBS."""
        try:
            event_name = str(eventData["event_name"])
            data = eventData["event_data"]
            triggerName = data["triggerName"].replace(" ", "_")
            assert "scene-switcher-" in event_name
            assert triggerName
        except:  # noqa: E722
            return

        match event_name:
            case "scene-switcher-alert":
                if alert := getattr(self.alert, triggerName, None):
                    await self.alert.queue.put((alert, data))
                    _LOGGER.info(
                        "Adding alert '%s' to queue. Queue size: %s",
                        triggerName,
                        str(self.alert.queue.qsize()),
                    )

            case "scene-switcher-transition":
                if transition := getattr(self.transition, triggerName, None):
                    await self.transition.queue.put((transition, data))
                    _LOGGER.info(
                        "Adding transition '%s' to queue. Queue size: %s",
                        triggerName,
                        str(self.transition.queue.qsize()),
                    )

            case "scene-switcher-audio":
                if triggerName == "Comms":
                    _LOGGER.info(
                        "Voice Visuals set enabled to: %s", str(data.get("mute"))
                    )
                    await self.action.Voice_Visuals(data.get("mute"))
                if triggerName == "Music":
                    _LOGGER.info(
                        "Music Audio set enabled to: %s", str(data.get("mute"))
                    )
                    await self.action.Music_Visuals(data.get("mute"))


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

import asyncio
import logging

import simpleobsws

from actions import Action
from alerts import Alert
from const import OBS, OFF, ON, Audio, Group, Scene_Item, Transition
from data import Data
from helpers import Helpers
from overlays import Overlay
from secret import Secret

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
        self.overlay = Overlay(self.action)
        self.overlay_switching_task: asyncio.Task | None = None
        self.alert = Alert(self.action)

    async def setup(self):
        await self.trigger_websocket()
        self.alert_worker_task = asyncio.create_task(self.alert._alert_worker())

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
                    self.CurrentSceneTransitionChanged,
                    "CurrentSceneTransitionChanged",
                )
                self.websocket.register_event_callback(
                    self.SceneItemEnableStateChanged,
                    "SceneItemEnableStateChanged",
                )
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
        except:  # noqa: E722
            return

        if event_name != "overlay-alert":
            return

        triggerName = eventData["event_data"].get("triggerName", "").replace(" ", "_")
        alert = getattr(self.alert, triggerName, None)

        if alert:
            await self.alert.alert_queue.put((alert, eventData["event_data"]))
            _LOGGER.info(
                "Adding alert '%s' to queue. Queue size: %s",
                triggerName,
                str(self.alert.alert_queue.qsize()),
            )

    async def CurrentSceneTransitionChanged(self, eventData):
        """OBS Scene Transition changed."""
        try:
            transition_name = str(eventData["transitionName"])
        except:  # noqa: E722
            return

        _LOGGER.debug("Transition changed to: %s", transition_name)

        if not (transition_name.startswith(("OL_", "A_"))):
            return

        if transition_name.startswith("OL_"):
            overlay = getattr(self.overlay, transition_name.removeprefix("OL_"), None)
            if overlay:
                if self.overlay_switching_task:
                    self.overlay_switching_task.cancel()
                    self.overlay_switching_task = None

                self.overlay_switching_task = asyncio.create_task(overlay())

        if transition_name.startswith("A_"):
            try:
                audio = Transition(transition_name)
                action, _input = audio.name.split("_", 1)
                input = Audio[_input]
                mute = action == "MUTE"
                asyncio.create_task(self.helper.toggle_audio_input(input, mute))
            except:  # noqa: E722
                return

    async def SceneItemEnableStateChanged(self, eventData):
        """OBS Scene Item was hidden or shown."""
        try:
            item_id = int(eventData["sceneItemId"])
            item_enabled = bool(eventData["sceneItemEnabled"])
        except:  # noqa: E722
            return

        if item_id == self.data.group_item[Group.EXTRA][Scene_Item.VOICE_VISUALS]:
            _LOGGER.info("Voice Visuals set enabled to: %s", str(item_enabled))
            await self.action.Voice_Visuals(item_enabled)

        elif item_id == self.data.group_item[Group.EXTRA][Scene_Item.MUSIC_AUDIO]:
            _LOGGER.info("Music Audio set enabled to: %s", str(item_enabled))
            self.action.Audio(Audio.MUSIC, not item_enabled)


def main():
    overlay_manager = Overlay_Manager()
    loop = asyncio.new_event_loop()

    _LOGGER.info("Starting event loop, scheduling OBS WebSocket and Alerts Queue setup...")
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

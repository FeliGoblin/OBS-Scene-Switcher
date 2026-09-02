import asyncio
import logging

import simpleobsws

from actions import Action
from alerts import Alert
from const import OBS, OFF, ON
from helpers import Helpers
from secret import Secret
from transitions import Transition

_LOGGER = logging.getLogger("WebSocket")


class WebSocket:
    def __init__(self, helper: Helpers, action: Action, transition: Transition, alert: Alert):
        self.client: simpleobsws.WebSocketClient | None = None
        self.reconnect_task: asyncio.Task | None = None
        self.connected: bool = False
        self.helper = helper
        self.action = action
        self.transition = transition
        self.alert = alert

    async def _trigger(self):
        if self.client:
            await self.config_status(OFF)
            return
        self.reconnect_task = asyncio.create_task(
            self.connect_obs()
        )

    async def config_status(self, toggle: bool) -> None:
        if not toggle:
            # if self.client and self.client.is_identified():
            if self.client:
                await self.client.disconnect()
            if self.reconnect_task:
                self.reconnect_task.cancel()
            self.client = None
            self.reconnect_task = None
        self.connected = toggle

    async def connect_obs(self) -> None:
        """Set up async OBS WebSocket client and get scene item IDs."""
        attempt = 0
        disconnected = False

        self.client = simpleobsws.WebSocketClient(
            url=Secret.OBS_WS_URL, password=Secret.OBS_WS_PWD
        )

        # Adding the WS session to the helper now that one is created.
        self.helper.websocket = self.client

        while True:
            if self.connected:
                if self.client and self.client.is_identified():
                    _LOGGER.debug("OBS WebSocket identified.")
                    await asyncio.sleep(OBS.DELAY)
                    continue
                _LOGGER.warning(
                    "OBS WebSocket disconnected, attempting reconnect %s...",
                    attempt + 1,
                )
                self.connected = False
                disconnected = True

            if attempt >= OBS.RETRIES:
                _LOGGER.warning("Connection failed. Stopping attempts.")
                await self.config_status(OFF)
                break
            attempt += 1

            _LOGGER.info("Attempting to connect to OBS WebSocket...")

            try:
                await self.client.connect()
                await self.client.wait_until_identified()

                _LOGGER.info("Connected to OBS!")
                attempt = 0
                disconnected = False
                await self.config_status(ON)

                # Register events to listen for.
                self.client.register_event_callback(
                    self.CustomEvent,
                    "CustomEvent",
                )

                await self.helper.get_obs_item_ids()
                await self.helper.get_obs_audio_inputs()

            except Exception:
                _LOGGER.exception("OBS connection failed")
                if not disconnected:
                    await self.config_status(OFF)
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

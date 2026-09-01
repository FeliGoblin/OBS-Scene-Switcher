import asyncio
import logging

import simpleobsws

from const import (
    OBS,
    Audio,
    Filter,
    Group,
    Scene,
    Scene_Item,
    Transition,
)
from data import Data

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger("Helpers")


class Helpers:
    def __init__(self, data: Data):
        self.data = data
        self.websocket: simpleobsws.WebSocketClient | None = None

    @classmethod
    async def sleep_ms(cls, time: float):
        await asyncio.sleep(time * 0.001)

    async def call_vendor_request(self, event_name: str, event_data: dict) -> dict:
        await self.websocket.call(
            simpleobsws.Request(
                "CallVendorRequest",
                {
                    "vendorName": "obs-browser",
                    "requestType": "emit_event",
                    "requestData": {"event_name": event_name, "event_data": event_data},
                },
            )
        )

    async def set_transition(self, transition_name: Transition):
        await self.websocket.call(
            simpleobsws.Request(
                "CallVendorRequest",
                {
                    "vendorName": "obs-browser",
                    "requestType": "emit_event",
                    "requestData": {
                        "event_name": "overlay-transition",
                        "event_data": {
                            "triggerName": transition_name.value
                        }
                    },
                },
            )
        )

    async def set_visibility(
        self, scene: Scene | Group, item: Scene_Item | Group, visibility: bool
    ):
        await self.websocket.call(
            simpleobsws.Request(
                "SetSceneItemEnabled",
                {
                    "sceneName": scene.value,
                    "sceneItemId": (
                        self.data.scene_item.get(scene, {}).get(item.value)
                        or self.data.group_item.get(scene, {}).get(item.value)
                    ),
                    "sceneItemEnabled": visibility,
                },
            )
        )

    async def set_filter_enabled(
        self, source: Group, filter_name: Filter, enable: bool
    ) -> None:
        await self.websocket.call(
            simpleobsws.Request(
                "SetSourceFilterEnabled",
                {
                    "sourceName": source.value,
                    "filterName": filter_name.value,
                    "filterEnabled": enable,
                },
            )
        )

    async def trigger_media_action(
        self, input_name, action
    ) -> None:
        await self.websocket.call(
            simpleobsws.Request(
                "TriggerMediaInputAction",
                {
                    "inputName": input_name,
                    "mediaAction": action
                },
            )
        )

    async def toggle_audio_input(self, input: Audio, mute: bool):
        diff = OBS.MAX_VOLUME - OBS.MIN_VOLUME
        step = diff / OBS.MUTE_STEPS

        if not mute:
            await self.websocket.call(
                simpleobsws.Request(
                    "SetInputVolume", {"inputName": input, "inputVolumeDb": OBS.MIN_VOLUME}
                )
            )

            await self.websocket.call(
                simpleobsws.Request(
                    "SetInputMute", {"inputName": input, "inputMuted": False}
                )
            )

        for i in range(1, OBS.MUTE_STEPS + 1) if mute else range(OBS.MUTE_STEPS - 1, -1, -1):
            await self.websocket.call(
                simpleobsws.Request(
                    "SetInputVolume",
                    {
                        "inputName": input,
                        "inputVolumeDb": -((step * i) - OBS.MAX_VOLUME),
                    },
                )
            )
            await self.sleep_ms(OBS.MUTE_TIME_MS / OBS.MUTE_STEPS)

        if mute:
            await self.websocket.call(
                simpleobsws.Request(
                    "SetInputMute", {"inputName": input, "inputMuted": True}
                )
            )

    async def get_obs_item_ids(self) -> None:
        self.data.scene_item.clear()
        for scene in Scene:
            lst = await self.get_scene_item_list(scene.value)
            if lst:
                self.data.scene_item[scene] = {
                    item["sourceName"]: item["sceneItemId"] for item in lst
                }

        self.data.group_item.clear()
        for group in Group:
            lst = await self.get_scene_item_list(group.value, group=True)
            if lst:
                self.data.group_item[group] = {
                    item["sourceName"]: item["sceneItemId"] for item in lst
                }

    async def get_obs_audio_inputs(self) -> None:
        self.data.audio_input.clear()
        for input in Audio:
            volume = await self.get_input_volume(input)
            if volume:
                self.data.audio_input[input] = {
                    "level": volume[0],
                    "mute": volume[1],
                }

    async def get_input_volume(self, input) -> list | None:
        volume = await self.websocket.call(
            simpleobsws.Request("GetInputVolume", {"inputName": input})
        )

        mute = await self.websocket.call(
            simpleobsws.Request("GetInputMute", {"inputName": input})
        )

        if not (
            isinstance(volume, simpleobsws.RequestResponse)
            and volume.has_data()
            and isinstance(mute, simpleobsws.RequestResponse)
            and mute.has_data()
        ):
            return None

        return [
            volume.responseData.get("inputVolumeDb"),
            mute.responseData.get("inputMuted"),
        ]

    async def get_scene_item_list(self, scene_name, *, group=False) -> list | None:
        request_response = await self.websocket.call(
            simpleobsws.Request(
                "GetGroupSceneItemList" if group else "GetSceneItemList",
                {"sceneName": scene_name},
            )
        )
        if (
            isinstance(request_response, simpleobsws.RequestResponse)
            and request_response.has_data()
        ):
            return request_response.responseData.get("sceneItems")
        return None

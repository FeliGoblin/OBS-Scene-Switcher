import asyncio
import logging

from const import (
    HIDE,
    MUTE,
    OFF,
    ON,
    SHOW,
    UNMUTE,
    Audio,
    Filter,
    Group,
    Scene,
    Scene_Item,
    Transition,
)
from data import Data
from helpers import Helpers

logging.basicConfig(level=logging.INFO)
_LOGGER = logging.getLogger("Actions")

sleep = Helpers.sleep_ms


class Action:
    def __init__(self, helper: Helpers, data: Data):
        self.helper = helper
        self.data = data
        self.Live = self._Live(self.helper)
        self.Idle = self._Idle(self.helper)
        self.Alert = self._Alert(self.helper)

    def Audio(self, input, mute):
        asyncio.create_task(self.helper.toggle_audio_input(input, mute))

    async def Trigger_Alert(self, message: str, submessage: str, duration_ms: int):
        await self.Alert.Set_Message(message, submessage)
        await sleep(20)

        await self.Alert.Text_Opacity(SHOW)
        await sleep(500)

        await self.Alert.Alert_Sound()
        await sleep(500)

        await self.Alert.Message_Typing(SHOW)
        await sleep(1200)

        if submessage:
            await self.Alert.Submessage_Typing(SHOW)
            await sleep(1500)

        await sleep(duration_ms)

        if submessage:
            await self.Alert.Submessage_Typing(HIDE)
            await sleep(500)

        await self.Alert.Message_Typing(HIDE)
        await sleep(1800)

        await self.Alert.Text_Opacity(HIDE)
        await sleep(100)

    async def Show_Idle_Overlay(self, text: Transition, enable_camera: bool) -> None:
        overlay_on = self.data.idle_overlay_enabled
        cam_on = self.data.idle_camera_enabled

        # --- Live -> Idle ---
        if not overlay_on:
            await self.Idle.Particles(SHOW)
            await sleep(1000)

            await self.Live.Content_Blur(ON)
            await self.Idle.Set_Text(text)
            await sleep(500)

            await self.Idle.Text_Opacity(SHOW)
            await sleep(1000)

            await self.Idle.Text_Typing(SHOW)
            await sleep(1200)

            self.Audio(Audio.GAME, MUTE)

            if enable_camera:
                await self.Idle.Camera_Slide(SHOW)
                await sleep(800)

                await self.Idle.Camera_Visibility(SHOW)
                await sleep(1000)

                self.data.idle_camera_enabled = True

            await self.Idle.Background(SHOW)
            await sleep(1800)

            await self.Idle.Foreground_Sources(enable_camera, SHOW)

            self.data.idle_overlay_enabled = True
            return

        # From here on: overlay is already on. Only camera state may change.

        if enable_camera == cam_on:
            # Hard reset / ensure everything is set correctly (no animation)
            await self.Idle.Foreground_Sources(not enable_camera, HIDE)
            await sleep(20)

            await self.Idle.Camera_Slide(enable_camera)
            await sleep(20)

            await self.Idle.Camera_Visibility(enable_camera)
            await sleep(20)

            await self.Idle.Foreground_Sources(enable_camera, SHOW)
            return

        # Hide current foreground set first
        await self.Idle.Foreground_Sources(not enable_camera, HIDE)

        if enable_camera and not cam_on:
            # Idle w/o Cam -> Idle w/ Cam
            await sleep(600)

            await self.Idle.Camera_Slide(SHOW)
            await sleep(800)

            await self.Idle.Camera_Visibility(SHOW)
            await sleep(1500)

        else:
            # Idle w/ Cam -> Idle w/o Cam
            await sleep(200)

            await self.Idle.Camera_Visibility(HIDE)
            await sleep(1200)

            await self.Idle.Camera_Slide(HIDE)
            await sleep(1500)

        await self.Idle.Foreground_Sources(enable_camera, SHOW)
        self.data.idle_camera_enabled = enable_camera

    async def Hide_Idle_Overlay(self) -> None:
        overlay_on = self.data.idle_overlay_enabled
        cam_on = self.data.idle_camera_enabled
        force_reassert = False

        if not overlay_on:
            # Hard reset / ensure everything is off (no animation)
            force_reassert = True

        async def _sleep(time: int) -> None:
            if force_reassert:
                # Set rapidly if hard resetting.
                await sleep(20)
                return
            await sleep(time)

        # --- Idle -> Live ---
        await self.Idle.Foreground_Sources(True, HIDE)
        await self.Idle.Foreground_Sources(False, HIDE)
        await _sleep(800)

        await self.Idle.Background(HIDE)
        self.Audio(Audio.GAME, UNMUTE)

        if cam_on or force_reassert:
            await _sleep(400)

            await self.Idle.Camera_Visibility(HIDE)
            await _sleep(1200)

            await self.Idle.Camera_Slide(HIDE)

        await _sleep(300)

        await self.Idle.Text_Typing(HIDE)
        await _sleep(1800)

        await self.Idle.Text_Opacity(HIDE)
        await _sleep(100)

        await self.Live.Content_Blur(OFF)
        await _sleep(1000)

        await self.Idle.Particles(HIDE)

        self.data.idle_overlay_enabled = False
        self.data.idle_camera_enabled = False

    async def Voice_Visuals(self, visibility: bool):
        self.Audio(Audio.COMMS, not visibility)
        self.Audio(Audio.TTS1, not visibility)
        for item in ("DISCORD", "GOBLIN", "SPEECH_BUBBLE"):
            await self.helper.set_visibility(
                Scene[item],
                Group[item],
                visibility,
            )

    class _Alert:
        def __init__(self, helper: Helpers):
            self.helper = helper

        async def Set_Message(self, message: str, submessage: str):
            _LOGGER.debug("Setting Alert Message")
            await self.helper.call_vendor_request(
                "overlay-alert",
                {
                    "trigger": "alert_message",
                    "message": message,
                    "submessage": submessage,
                },
            )

        async def Text_Opacity(self, visibility: bool):
            _LOGGER.debug("Alert text opacity: " + "Showing" if visibility else "Hiding")
            await self.helper.call_vendor_request(
                "overlay-alert", {"trigger": "alert_opacity", "visibility": visibility}
            )

        async def Message_Typing(self, reveal: bool):
            _LOGGER.debug("Alert message typing: " + "Typing" if reveal else "Untyping")
            await self.helper.call_vendor_request(
                "overlay-alert", {"trigger": "alert_msg_typing", "reveal": reveal}
            )

        async def Submessage_Typing(self, reveal: bool):
            _LOGGER.debug("Alert submessage typing: " + "Typing" if reveal else "Untyping")
            await self.helper.call_vendor_request(
                "overlay-alert", {"trigger": "alert_submsg_typing", "reveal": reveal}
            )

        async def Alert_Sound(self):
            _LOGGER.debug("Playing Alert Sound")
            await self.helper.trigger_media_action(
                "Alert", "OBS_WEBSOCKET_MEDIA_INPUT_ACTION_RESTART"
            )

    class _Live:
        def __init__(self, helper: Helpers):
            self.helper = helper

        async def Content_Blur(self, blur: bool):
            _LOGGER.debug("%s%s", "B" if blur else "Unb", "luring content")
            await self.helper.set_filter_enabled(
                Scene.GAMES,
                Filter.SHOW_BLUR if blur else Filter.HIDE_BLUR,
                True,
            )

        async def Fullscreen_Cam(self, visibility: bool):
            _LOGGER.debug("Fullscreen Cam: " + "Enabled" if visibility else "Disabled")
            await self.helper.set_visibility(
                Group.WOW_WRAP,
                Scene_Item.FULLSCREEN_CAM,
                visibility,
            )
            await self.helper.set_visibility(
                Scene.CHAT_COVER,
                Scene_Item.WOW,
                visibility,
            )

    class _Idle:
        def __init__(self, helper: Helpers):
            self.helper = helper

        async def Foreground_Sources(self, cam: bool, visibility: bool):
            _LOGGER.debug(
                "Foreground Sources: " + "Showing"
                if visibility
                else "Hiding" + " with"
                if cam
                else " without" + " cam"
            )
            await self.helper.set_visibility(
                Scene.IDLE,
                Group.IDLE_CAM if cam else Group.IDLE_NOCAM,
                visibility,
            )

        async def Set_Text(self, text: Transition):
            _LOGGER.debug("Setting text")
            await self.helper.set_transition(text)

        async def Camera_Visibility(self, visibility: bool):
            _LOGGER.debug("Camera Visibility: " + "Showing" if visibility else "Hiding")
            await self.helper.set_visibility(
                Scene.IDLE,
                Scene_Item.CAMERA,
                visibility,
            )

        async def Background(self, visibility: bool):
            _LOGGER.debug("Background: " + "Showing" if visibility else "Hiding")
            await self.helper.set_transition(
                Transition.SHOW_BACKGROUND if visibility else Transition.HIDE_BACKGROUND
            )

        async def Particles(self, visibility: bool):
            _LOGGER.debug("Particles: " + "Showing" if visibility else "Hiding")
            await self.helper.set_transition(
                Transition.SHOW_PARTICLES if visibility else Transition.HIDE_PARTICLES
            )

        async def Text_Opacity(self, visibility: bool):
            _LOGGER.debug("Text opacity: " + "Showing" if visibility else "Hiding")
            await self.helper.set_transition(
                Transition.SHOW_TEXT if visibility else Transition.HIDE_TEXT
            )

        async def Text_Typing(self, reveal: bool):
            _LOGGER.debug("Text typing: " + "Typing" if reveal else "Untyping")
            await self.helper.set_transition(
                Transition.TYPE_TEXT if reveal else Transition.UNTYPE_TEXT
            )

        async def Camera_Slide(self, reveal: bool):
            _LOGGER.debug("Camera slide: " + "Showing" if reveal else "Hiding")
            await self.helper.set_transition(
                Transition.SHOW_CAMERA if reveal else Transition.HIDE_CAMERA
            )

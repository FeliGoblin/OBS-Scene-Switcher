import asyncio
import logging

from actions import Action
from const import END_SPN, RED_SPN, RED_STR
from const import Alert as Const_Alert

_LOGGER = logging.getLogger("Alerts")


class Alert:
    def __init__(self, action: Action):
        self.action = action
        self.alert_queue = asyncio.Queue()
        self.alert_worker_task: asyncio.Task | None = None

    async def _alert_worker(self):
        while True:
            alert, event_data = await self.alert_queue.get()
            try:
                await alert(event_data)
            except Exception:
                _LOGGER.exception("Alert playback failed")
            finally:
                self.alert_queue.task_done()

    async def Subscription(self, data: dict):
        """Twitch Subscription."""
        if not (user := data.get("user")): return

        message = f"{RED_SPN}{user}{END_SPN} just subscribed"

        if not (tier := data.get("tier")):
            message += "!"

        if tier == "prime":
            message += " with "
        else:
            message += " at " 

        message += f"{tier.capitalize()}!"

        tenure = data.get("monthsTenure")

        try:
            if int(tenure) > 0:
                submessage = f"They've been subscribed for {tenure} months!"
        except:  # noqa: E722
            submessage = ""

        await self.action.Trigger_Alert(message, submessage, Const_Alert.SUBSCRIPTION_DURATION_MS.value)

    async def Raid(self, data: dict):
        """Twitch Raid."""
        message = f"{RED_SPN}{data.get("user", "Anonymous")}{END_SPN} raided with {RED_SPN}{data.get("viewers", "0")}{END_SPN} viewers!"

        await self.action.Trigger_Alert(message, "", Const_Alert.SUBSCRIPTION_DURATION_MS.value)

    async def Donation(self, data: dict):
        """Kofi Donation."""
        message = f"{RED_SPN}{data.get("from", "Anonymous")}{END_SPN} just donated {RED_SPN}{data.get("amount", "(unknown amount)")} {data.get("currency", "???")}{END_SPN}!"
        submessage = ""

        if data.get("isPublic") and (msg := data.get("message")) and msg != "%":
            submessage = msg

        if len(submessage) > 80:
            submessage = f"{submessage[:80]} [...]"

        await self.action.Trigger_Alert(message, submessage, Const_Alert.SUBSCRIPTION_DURATION_MS.value)

    async def Cheer(self, data: dict):
        """Twitch Cheer."""
        color = data.get("color")
        if not color or color != "%color%":
            color = RED_STR

        message = f"<span style='color:{color};'>{data.get("user", "Anonymous")}{END_SPN} just cheered with <span style='color:{color};'>{data.get("bits")} bits{END_SPN}!"
        submessage = ""

        if (msg := data.get("message")):
            submessage = msg

        if len(submessage) > 80:
            submessage = f"{submessage[:80]} [...]"

        await self.action.Trigger_Alert(message, submessage, Const_Alert.SUBSCRIPTION_DURATION_MS.value)

    async def Gift_Subscription(self, data: dict):
        """Twitch Gift Subscription."""
        message = f"{RED_SPN}{data.get("userName", "Anonymous")}{END_SPN} gifted a {data.get("tier", "").capitalize()} subscription to {RED_SPN}{data.get("recipientUserName", "Anonymous")}{END_SPN}!"

        await self.action.Trigger_Alert(message, "", Const_Alert.SUBSCRIPTION_DURATION_MS.value)

    async def Gift_Bomb(self, data: dict):
        """Twitch Cheer."""
        message = f"{RED_SPN}{data.get("userName", "Anonymous")}{END_SPN} just gifted {RED_SPN}{data.get("gifts")}{END_SPN} {data.get("tier", "").capitalize()} subscriptions!"

        await self.action.Trigger_Alert(message, "", Const_Alert.SUBSCRIPTION_DURATION_MS.value)


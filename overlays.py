from actions import Action
from const import HIDE, SHOW, Transition


class Overlay:
    def __init__(self, action: Action):
        self.action = action

    async def Starting_Soon_NoCam(self):
        await self.action.Show_Idle_Overlay(Transition.TEXT_STARTING_SOON, False)

    async def Starting_Soon_Cam(self):
        await self.action.Show_Idle_Overlay(Transition.TEXT_STARTING_SOON, True)

    async def Be_Right_Back_NoCam(self):
        await self.action.Show_Idle_Overlay(Transition.TEXT_BE_RIGHT_BACK, False)

    async def Be_Right_Back_Cam(self):
        await self.action.Show_Idle_Overlay(Transition.TEXT_BE_RIGHT_BACK, True)

    async def Stream_Ending_NoCam(self):
        await self.action.Show_Idle_Overlay(Transition.TEXT_STREAM_ENDING, False)

    async def Stream_Ending_Cam(self):
        await self.action.Show_Idle_Overlay(Transition.TEXT_STREAM_ENDING, True)

    async def Live(self):
        await self.action.Live.Fullscreen_Cam(HIDE)
        await self.action.Hide_Idle_Overlay()

    async def Fullscreen_Cam(self):
        await self.action.Live.Fullscreen_Cam(SHOW)
        await self.action.Hide_Idle_Overlay()

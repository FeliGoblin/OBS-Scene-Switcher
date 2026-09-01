from enum import Enum, IntEnum, StrEnum

ON = True
OFF = False
SHOW = True
HIDE = False
MUTE = True
UNMUTE = False
RED_STR = "#e04820"
RED_SPN = f"<span style='color:{RED_STR};'>"
END_SPN = "</span>"


class OBS(IntEnum):
    DELAY = 20  # seconds between connection checks
    RETRIES = 3 # number of retries after a disconnect
    MAX_VOLUME = -1.0
    MIN_VOLUME = -100.0
    MUTE_STEPS = 15
    MUTE_TIME_MS = 2500

class Alert(Enum):
    SUBSCRIPTION_DURATION_MS = 5000

class Transition(StrEnum):
    TEXT_STARTING_SOON = "BR_Text_Starting_Soon"
    TEXT_BE_RIGHT_BACK = "BR_Text_Be_Right_Back"
    TEXT_STREAM_ENDING = "BR_Text_Stream_Ending"

    SHOW_BACKGROUND = "BR_Show_Background"
    HIDE_BACKGROUND = "BR_Hide_Background"
    SHOW_PARTICLES = "BR_Show_Particles"
    HIDE_PARTICLES = "BR_Hide_Particles"
    SHOW_CAMERA = "BR_Show_Camera"
    HIDE_CAMERA = "BR_Hide_Camera"
    SHOW_TEXT = "BR_Show_Text"
    HIDE_TEXT = "BR_Hide_Text"
    TYPE_TEXT = "BR_Type_Text"
    UNTYPE_TEXT = "BR_Untype_Text"

    MUTE_GAME = "A_Mute_Game"
    UNMUTE_GAME = "A_Unmute_Game"
    MUTE_MUSIC = "A_Mute_Music"
    UNMUTE_MUSIC = "A_Unmute_Music"
    MUTE_COMMS = "A_Mute_Comms"
    UNMUTE_COMMS = "A_Unmute_Comms"
    MUTE_TTS1 = "A_Mute_TTS1"
    UNMUTE_TTS1 = "A_Unmute_TTS1"
    MUTE_TTS2 = "A_Mute_TTS2"
    UNMUTE_TTS2 = "A_Unmute_TTS2"


class Group(StrEnum):
    WOW_WRAP = "WoW Wrap"
    SILKSONG_WRAP = "Silksong Wrap"
    IDLE_NOCAM = "Idle ➔ No Cam"
    IDLE_CAM = "Idle ➔ Cam"
    DISCORD = "Reactive Wrap"
    GOBLIN = "Goblin Wrap"
    SPEECH_BUBBLE = "SpeechBubble Wrap"
    EXTRA = "Extra"


class Scene(StrEnum):
    LIVE = "Live"
    IDLE = "Idle Wrap"
    GAMES = "Games Wrap"
    SPEECH_BUBBLE = "Speech Bubble Wrap"
    GOBLIN = "Goblin"
    DISCORD = "Discord Wrap"
    CHAT_COVER = "Chat Cover"


class Scene_Item(StrEnum):
    DISCORD = "Reactive"
    CAMERA = "Webcam Wrap"
    FULLSCREEN_CAM = "Webcam Fullscreen"
    VOICE_VISUALS = "Comms Toggle"
    MUSIC_AUDIO = "Firefox Toggle"
    WOW = "World of Warcraft"


class Filter(StrEnum):
    SHOW_BLUR = "Show_Blur"
    HIDE_BLUR = "Hide_Blur"


class Audio(StrEnum):
    GAME = "Game"
    MUSIC = "Firefox"
    COMMS = "Comms"
    TTS1 = "TTS 1"
    TTS2 = "TTS 2"

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
    RETRIES = 3  # number of retries after a disconnect
    MAX_VOLUME = -1
    MIN_VOLUME = -100
    MUTE_STEPS = 15
    MUTE_TIME_MS = 2500


class Alert(Enum):
    DURATION_MS = 5000


class Idle_Text(StrEnum):
    STARTING_SOON = "STARTING SOON"
    BE_RIGHT_BACK = "BE RIGHT BACK"
    STREAM_ENDING = "STREAM ENDING"


class Group(StrEnum):
    WOW_WRAP = "WoW Wrap"
    SILKSONG_WRAP = "Silksong Wrap"
    IDLE_NOCAM = "Idle ➔ No Cam"
    IDLE_CAM = "Idle ➔ Cam"
    DISCORD = "Reactive Wrap"
    GOBLIN = "Goblin Wrap"
    SPEECH_BUBBLE = "SpeechBubble Wrap"
    EXTRA = "Extra"
    MUSIC = "Music"


class Scene(StrEnum):
    LIVE = "Live"
    IDLE = "Idle Wrap"
    GAMES = "Games Wrap"
    MUSIC = "Music Wrap"
    SPEECH_BUBBLE = "Speech Bubble Wrap"
    GOBLIN = "Goblin"
    DISCORD = "Discord Wrap"
    CHAT_COVER = "Chat Cover"


class Scene_Item(StrEnum):
    CAMERA = "Webcam Wrap"
    FULLSCREEN_CAM = "Webcam Fullscreen"
    WOW = "World of Warcraft"


class Filter(StrEnum):
    SHOW_BLUR = "Show_Blur"
    HIDE_BLUR = "Hide_Blur"


class Audio(StrEnum):
    GAME = "Game"
    MUSIC = "Chrome"
    COMMS = "Comms"
    TTS1 = "TTS 1"
    TTS2 = "TTS 2"

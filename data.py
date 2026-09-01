from const import Audio, Group, Scene


class Data:
    scene_item: dict[Scene, dict[str, int]] = {}
    group_item: dict[Group, dict[str, int]] = {}
    audio_input: dict[Audio, dict[str, float | bool]] = {}
    idle_camera_enabled: bool = False
    idle_overlay_enabled: bool = False

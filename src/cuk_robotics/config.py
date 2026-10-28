"""Project profile loading without importing or connecting hardware libraries."""
import json
from pathlib import Path


def load_hardware(path, project_root, *, require_devices=True, wrist_fourcc=None, include_cameras=True):
    if wrist_fourcc not in (None, "MJPG", "YUY2"):
        raise ValueError("Wrist camera FOURCC must be MJPG or YUY2.")
    profile = json.loads(Path(path).read_text(encoding="utf-8"))
    if set(profile) != {"robot", "teleop"}:
        raise ValueError("Hardware profile must contain robot and teleop.")
    for component in ("robot", "teleop"):
        settings = profile[component]
        for side in ("left_arm_config", "right_arm_config"):
            if require_devices and not settings.get(side, {}).get("port"):
                raise ValueError(f"Set {component}.{side}.port in configs/local/hardware.json.")
        directory = Path(settings["calibration_dir"])
        if not directory.is_absolute():
            directory = Path(project_root) / directory
        settings["calibration_dir"] = str(directory.resolve())
        if require_devices:
            for side in ("left", "right"):
                calibration = directory / f"{settings['id']}_{side}.json"
                if not calibration.is_file():
                    raise FileNotFoundError(f"Missing calibration: {calibration}")
    if not include_cameras:
        # Operation must ignore all camera settings, including per-arm cameras.
        profile["robot"]["cameras"] = {}
        for side in ("left_arm_config", "right_arm_config"):
            profile["robot"][side].pop("cameras", None)
        return profile
    cameras = profile["robot"].get("cameras", {})
    if set(cameras) != {"left_wrist", "right_wrist", "top"}:
        raise ValueError("Expected left_wrist, right_wrist and top cameras.")
    if require_devices and any(camera.get("index_or_path") is None for camera in cameras.values()):
        raise ValueError("Set all camera indices in configs/local/hardware.json.")
    if wrist_fourcc is not None:
        for name in ("left_wrist", "right_wrist"):
            cameras[name]["fourcc"] = wrist_fourcc
    return profile

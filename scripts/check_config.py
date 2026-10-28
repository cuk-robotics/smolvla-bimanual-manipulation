"""Validate public hardware and recording inputs without connecting devices."""

import argparse
import json
import math
from pathlib import Path
import sys


ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cuk_robotics.config import load_hardware
from cuk_robotics.teleoperation.recording import build_recording_args


def positive_number(value, label, *, allow_zero=False, integer=False):
    if (type(value) not in (int, float) or not math.isfinite(value)
            or (integer and type(value) is not int)
            or value < 0 or (value == 0 and not allow_zero)):
        raise ValueError(f"Invalid {label}: expected a finite positive number (zero allowed: {allow_zero}).")


def validate_public_config(hardware, recording):
    """Check shareable inputs; never open devices, create datasets, or upload."""
    if set(hardware) != {"robot", "teleop"}:
        raise ValueError("Hardware must contain robot and teleop.")
    for component, expected in (("robot", "bi_so_follower"), ("teleop", "bi_so_leader")):
        settings = hardware[component]
        if settings.get("type") != expected or not settings.get("id"):
            raise ValueError(f"Invalid {component} type or id.")
        for side in ("left_arm_config", "right_arm_config"):
            if side not in settings or settings[side].get("port") is not None:
                raise ValueError(f"Public {component}.{side}.port must be null.")
    cameras = hardware["robot"].get("cameras", {})
    if set(cameras) != {"left_wrist", "right_wrist", "top"}:
        raise ValueError("Exactly left_wrist, right_wrist and top cameras are required.")
    for name, camera in cameras.items():
        if camera.get("type") != "opencv" or camera.get("index_or_path") is not None:
            raise ValueError(f"Public {name} must be an unconfigured OpenCV camera.")
        for key in ("width", "height", "fps"):
            positive_number(camera.get(key), f"{name}.{key}", integer=True)
    for key in ("num_episodes", "episode_time_s", "reset_time_s"):
        positive_number(recording.get(key), key, allow_zero=key == "reset_time_s",
                        integer=key == "num_episodes")
    if recording.get("push_to_hub", False) is not False:
        raise ValueError("Automatic Hub uploads must remain disabled.")
    # The real recorder helper validates repo ID/task and only builds arguments.
    args, _, _ = build_recording_args(
        ROOT, recording["repo_id"], recording["single_task"],
        episodes=recording["num_episodes"], episode_seconds=recording["episode_time_s"],
        reset_seconds=recording["reset_time_s"],
    )
    if "--dataset.push_to_hub=false" not in args:
        raise ValueError("Recorder default must disable Hub upload.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--hardware", type=Path, default=ROOT / "configs/hardware/so101_bimanual.example.json")
    parser.add_argument("--recording", type=Path, default=ROOT / "configs/recording/beverage.json")
    args = parser.parse_args()
    try:
        hardware = load_hardware(args.hardware, ROOT, require_devices=False)
        recording = json.loads(args.recording.read_text(encoding="utf-8"))
        validate_public_config(hardware, recording)
    except (OSError, ValueError, AttributeError, KeyError, TypeError) as exc:
        parser.error(str(exc))
    print("Public hardware template and recording defaults OK: 2 arms, 3 cameras, uploads disabled.")
    print("This check never connects devices and does not certify hardware safety.")


if __name__ == "__main__":
    main()

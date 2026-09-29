"""Check offline scaffold settings only; never import or connect device backends."""

import argparse
import json
from pathlib import Path


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / "configs" / "project.example.json"


def validate_offline_config(config: dict) -> None:
    """Reject non-offline settings; this is not a hardware safety interlock."""
    if config.get("mode") != "dry_run" or config.get("hardware_enabled") is not False:
        raise ValueError("Only dry_run with hardware_enabled=false is supported.")
    if config.get("hugging_face", {}).get("push_to_hub") is not False:
        raise ValueError("Automatic Hub uploads must remain disabled.")
    if set(config.get("cameras", {})) != {"left_wrist", "right_wrist", "top"}:
        raise ValueError("Exactly left_wrist, right_wrist and top cameras are required.")
    if set(config.get("robot", {}).get("arms", {})) != {"left", "right"}:
        raise ValueError("Both left and right arms are required.")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    args = parser.parse_args()
    try:
        config = json.loads(args.config.read_text(encoding="utf-8"))
        validate_offline_config(config)
    except (OSError, ValueError, AttributeError, TypeError) as exc:
        parser.error(str(exc))
    print("Offline configuration OK: 2 arms, 3 cameras, hardware and uploads disabled.")
    print("No devices connected. Hardware integration and calibration remain unverified.")


if __name__ == "__main__":
    main()

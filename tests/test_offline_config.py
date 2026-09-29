"""Regression checks for offline-only scaffold defaults and required inputs."""

import copy
import importlib.util
import json
from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_config", ROOT / "scripts" / "check_config.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class OfflineConfigTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "configs" / "project.example.json").read_text(encoding="utf-8"))

    def test_example_is_offline(self):
        CHECK.validate_offline_config(self.config)

    def test_rejects_motion_and_ambiguous_flags(self):
        for value in (True, "false", 0, None):
            with self.subTest(value=value):
                config = copy.deepcopy(self.config)
                config["hardware_enabled"] = value
                with self.assertRaises(ValueError):
                    CHECK.validate_offline_config(config)

    def test_rejects_non_dry_run(self):
        self.config["mode"] = "live"
        with self.assertRaises(ValueError):
            CHECK.validate_offline_config(self.config)

    def test_rejects_upload(self):
        self.config["hugging_face"]["push_to_hub"] = True
        with self.assertRaises(ValueError):
            CHECK.validate_offline_config(self.config)

    def test_rejects_missing_camera_or_arm(self):
        for section, key in (("cameras", "top"), ("arms", "right")):
            with self.subTest(section=section):
                config = copy.deepcopy(self.config)
                target = config["cameras"] if section == "cameras" else config["robot"]["arms"]
                del target[key]
                with self.assertRaises(ValueError):
                    CHECK.validate_offline_config(config)


if __name__ == "__main__":
    unittest.main()

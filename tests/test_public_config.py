"""Check real shared profiles instead of the retired design-only scaffold."""
import copy
import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("check_config", ROOT / "scripts/check_config.py")
CHECK = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(CHECK)


class PublicConfigTests(unittest.TestCase):
    def setUp(self):
        self.hardware = json.loads((ROOT / "configs/hardware/so101_bimanual.example.json").read_text(encoding="utf-8"))
        self.recording = json.loads((ROOT / "configs/recording/beverage.json").read_text(encoding="utf-8"))

    def test_public_defaults_work_without_device_imports(self):
        # A clean subprocess also detects imports hidden by another test's cache.
        code = "import runpy,sys; sys.argv=['check_config']; runpy.run_path('scripts/check_config.py',run_name='__main__'); assert not any(n.split('.')[0] in {'lerobot','cv2','torch'} for n in sys.modules)"
        result = subprocess.run([sys.executable, "-c", code], cwd=ROOT, capture_output=True, text=True)
        self.assertEqual(result.returncode, 0, result.stderr)

    def test_machine_values_are_rejected_in_public_template(self):
        for component in ("robot", "teleop"):
            hardware = copy.deepcopy(self.hardware)
            hardware[component]["left_arm_config"]["port"] = "COM99"
            with self.subTest(component=component), self.assertRaises(ValueError):
                CHECK.validate_public_config(hardware, self.recording)
        self.hardware["robot"]["cameras"]["top"]["index_or_path"] = 0
        with self.assertRaises(ValueError):
            CHECK.validate_public_config(self.hardware, self.recording)

    def test_missing_arm_or_camera_is_rejected(self):
        for key in ("right_arm_config", "cameras"):
            hardware = copy.deepcopy(self.hardware)
            if key == "cameras":
                del hardware["robot"][key]["top"]
            else:
                del hardware["robot"][key]
            with self.subTest(key=key), self.assertRaises(ValueError):
                CHECK.validate_public_config(hardware, self.recording)

    def test_invalid_recording_values_and_upload_are_rejected(self):
        for key, value in (("num_episodes", True), ("num_episodes", 1.5),
                           ("episode_time_s", float("nan")), ("episode_time_s", 0),
                           ("reset_time_s", -1), ("push_to_hub", True),
                           ("repo_id", "invalid"), ("single_task", " ")):
            with self.subTest(key=key, value=value), self.assertRaises(ValueError):
                CHECK.validate_public_config(self.hardware, {**self.recording, key: value})

    def test_invalid_video_dimensions_and_fps_are_rejected(self):
        for key, value in (("width", 0), ("height", -1), ("fps", float("inf"))):
            hardware = copy.deepcopy(self.hardware)
            hardware["robot"]["cameras"]["top"][key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                CHECK.validate_public_config(hardware, self.recording)


if __name__ == "__main__":
    unittest.main()

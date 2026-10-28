"""Check profile portability and reject unconfigured devices without hardware imports."""
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("profile_config", ROOT / "src/cuk_robotics/config.py")
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


class HardwareProfileTests(unittest.TestCase):
    def test_relative_calibration_follows_checkout(self):
        with tempfile.TemporaryDirectory() as directory:
            profile = module.load_hardware(ROOT / "configs/hardware/so101_bimanual.example.json", directory, require_devices=False)
            self.assertEqual(profile["robot"]["calibration_dir"], str((Path(directory) / "calibration/so101").resolve()))
            self.assertEqual(profile["teleop"]["calibration_dir"], profile["robot"]["calibration_dir"])

    def test_template_cannot_start_hardware(self):
        with self.assertRaisesRegex(ValueError, "port"):
            module.load_hardware(ROOT / "configs/hardware/so101_bimanual.example.json", ROOT)

    def test_wrist_format_override_preserves_file_top_and_other_settings(self):
        source = ROOT / "configs/hardware/so101_bimanual.example.json"
        before = source.read_bytes()
        baseline = module.load_hardware(source, ROOT, require_devices=False)
        overridden = module.load_hardware(source, ROOT, require_devices=False, wrist_fourcc="MJPG")
        self.assertEqual(source.read_bytes(), before)
        self.assertEqual(overridden["teleop"], baseline["teleop"])
        self.assertEqual(overridden["robot"]["cameras"]["top"], baseline["robot"]["cameras"]["top"])
        for name in ("left_wrist", "right_wrist"):
            self.assertEqual(overridden["robot"]["cameras"][name], {**baseline["robot"]["cameras"][name], "fourcc": "MJPG"})
            del overridden["robot"]["cameras"][name]["fourcc"]
        self.assertEqual(overridden, baseline)
        self.assertEqual(json.loads(before)["robot"]["cameras"], baseline["robot"]["cameras"])

    def test_invalid_wrist_format_fails_before_reading_profile(self):
        with self.assertRaisesRegex(ValueError, "FOURCC"):
            module.load_hardware("does-not-exist.json", ROOT, wrist_fourcc="INVALID")


if __name__ == "__main__":
    unittest.main()

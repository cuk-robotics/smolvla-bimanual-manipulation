"""Verify camera-free operation without opening cameras or motor ports."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("operation_profile", ROOT / "src/cuk_robotics/config.py")
PROFILE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(PROFILE)


class OperationProfileTests(unittest.TestCase):
    def test_ignores_missing_invalid_and_per_arm_cameras_preserving_motor_settings(self):
        template = json.loads((ROOT / "configs/hardware/so101_bimanual.example.json").read_text())
        for cameras in (None, {}, {"broken": {"backend": "INVALID", "index_or_path": None}}):
            with self.subTest(cameras=cameras), tempfile.TemporaryDirectory() as directory:
                source = Path(directory) / "hardware.json"
                profile = json.loads(json.dumps(template))
                profile["robot"].pop("cameras")
                if cameras is not None:
                    profile["robot"]["cameras"] = cameras
                for side in ("left_arm_config", "right_arm_config"):
                    profile["robot"][side]["cameras"] = {"extra": {"type": "invalid"}}
                source.write_text(json.dumps(profile), encoding="utf-8")
                before = source.read_bytes()
                result = PROFILE.load_hardware(source, ROOT, require_devices=False, include_cameras=False)
                self.assertEqual(result["robot"]["cameras"], {})
                for side in ("left_arm_config", "right_arm_config"):
                    self.assertEqual(result["robot"][side], template["robot"][side])
                self.assertEqual(result["teleop"]["left_arm_config"], template["teleop"]["left_arm_config"])
                self.assertEqual(source.read_bytes(), before)
                with self.assertRaisesRegex(ValueError, "Expected"):
                    PROFILE.load_hardware(source, ROOT, require_devices=False)

    def test_operation_still_requires_ports_and_calibration(self):
        with self.assertRaisesRegex(ValueError, "port"):
            PROFILE.load_hardware(ROOT / "configs/hardware/so101_bimanual.example.json", ROOT, include_cameras=False)
        with tempfile.TemporaryDirectory() as directory:
            source = Path(directory) / "hardware.json"
            profile = json.loads((ROOT / "configs/hardware/so101_bimanual.example.json").read_text())
            for component in ("robot", "teleop"):
                for side in ("left_arm_config", "right_arm_config"):
                    profile[component][side]["port"] = "COM1"
            source.write_text(json.dumps(profile), encoding="utf-8")
            with self.assertRaisesRegex(FileNotFoundError, "Missing calibration"):
                PROFILE.load_hardware(source, directory, include_cameras=False)


@unittest.skipUnless(all(importlib.util.find_spec(name) for name in ("lerobot", "draccus", "yaml")), "Requires LeRobot environment")
class OperationCliTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        sys.path.insert(0, str(ROOT / "src"))
        from cuk_robotics.teleoperation import cli
        from lerobot.scripts import lerobot_teleoperate
        cls.cli = cli
        cls.official = lerobot_teleoperate

    def setUp(self):
        self.directory = tempfile.TemporaryDirectory()
        self.addCleanup(self.directory.cleanup)
        self.base = Path(self.directory.name)
        self.profile = json.loads((ROOT / "configs/hardware/so101_bimanual.example.json").read_text())
        self.profile["robot"]["cameras"] = {"invalid": {"type": "invalid"}}
        for component, ports in (("robot", ("COM13", "COM12")), ("teleop", ("COM14", "COM11"))):
            for side, port in zip(("left_arm_config", "right_arm_config"), ports):
                self.profile[component][side]["port"] = port
                if component == "robot":
                    self.profile[component][side]["cameras"] = {"invalid": {"type": "invalid"}}
        (self.base / "configs/local").mkdir(parents=True)
        (self.base / "configs/local/hardware.json").write_text(json.dumps(self.profile), encoding="utf-8")
        calibration = self.base / "calibration/so101"
        calibration.mkdir(parents=True)
        for component in ("robot", "teleop"):
            for side in ("left", "right"):
                (calibration / f"{self.profile[component]['id']}_{side}.json").write_text("{}")

    def run_cli(self, *args, dispatch=None):
        with patch.object(sys, "argv", ["run_robot.py", "--project-root", str(self.base), "operation", *args]), \
                patch.object(self.cli, "BASE", self.base), \
                patch.object(self.cli, "install_camera_layout", side_effect=AssertionError("Display layout called")), \
                patch.object(self.official, "main", side_effect=dispatch) as main, \
                patch.object(self.official, "make_robot_from_config", side_effect=AssertionError("Motor construction called")), \
                patch.object(self.official, "make_teleoperator_from_config", side_effect=AssertionError("Leader construction called")), \
                patch("cuk_robotics.teleoperation.rerun_display.start_local_viewer", side_effect=AssertionError("Viewer called")), \
                patch("cuk_robotics.teleoperation.rerun_display.install_display_logging", side_effect=AssertionError("Display logging called")), \
                contextlib.redirect_stdout(io.StringIO()):
            self.cli.main()
            return main.call_count

    def test_validate_only_ignores_cameras_without_dispatch(self):
        self.assertEqual(self.run_cli("--validate-only"), 0)

    def test_dispatch_passes_empty_cameras_and_preserves_both_pairs(self):
        configs = []

        def capture():
            configs.append(self.cli.draccus.parse(config_class=self.official.TeleoperateConfig, args=sys.argv[1:]))
            # Logging customization must leave the official processors untouched.
            teleop, _, _ = self.official.make_default_processors()
            self.assertEqual(len(teleop.steps), 1)
            self.assertEqual(teleop(({'left_shoulder_lift.pos': -113.275}, {})),
                             {'left_shoulder_lift.pos': -113.275})

        self.assertEqual(self.run_cli("--fps", "45", "--duration-s", "30", dispatch=capture), 1)
        config = configs[0]
        self.assertFalse(config.display_data)
        self.assertIsNone(config.display_ip)
        self.assertIsNone(config.display_port)
        self.assertEqual(config.robot.cameras, {})
        self.assertEqual(config.fps, 45)
        self.assertEqual(config.teleop_time_s, 30)
        for component in ("robot", "teleop"):
            for side in ("left_arm_config", "right_arm_config"):
                actual = getattr(getattr(config, component), side)
                self.assertEqual(actual.port, self.profile[component][side]["port"])
                if component == "robot":
                    self.assertEqual(actual.cameras, {})
                    self.assertEqual(actual.max_relative_target, self.profile[component][side]["max_relative_target"])
                    self.assertTrue(actual.disable_torque_on_disconnect)

    def test_default_rate_and_unlimited_duration(self):
        def capture():
            config = self.cli.draccus.parse(config_class=self.official.TeleoperateConfig, args=sys.argv[1:])
            self.assertEqual(config.fps, 60)
            self.assertIsNone(config.teleop_time_s)

        self.assertEqual(self.run_cli(dispatch=capture), 1)

    def test_verbose_warning_option_reaches_dispatch_without_changing_control(self):
        with patch("cuk_robotics.teleoperation.console_logging.readable_console") as console:
            self.assertEqual(self.run_cli("--verbose-target-warnings"), 1)
        console.assert_called_once_with(self.official, verbose=True)

    def test_camera_recording_and_invalid_duration_options_rejected(self):
        for args in (("--wrist-fourcc", "MJPG"), ("--push-to-hub",), ("--episodes", "1"), ("--duration-s", "nan"), ("--duration-s", "0")):
            with self.subTest(args=args), contextlib.redirect_stderr(io.StringIO()), self.assertRaises(SystemExit) as caught:
                self.run_cli(*args)
            self.assertEqual(caught.exception.code, 2)


if __name__ == "__main__":
    unittest.main()

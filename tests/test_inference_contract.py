"""Reject incompatible policy inputs before any robot connection."""
import importlib.util
from pathlib import Path
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("inference_contract", ROOT / "src/cuk_robotics/teleoperation/inference.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class InferenceContractTests(unittest.TestCase):
    def setUp(self):
        self.names = ["left_shoulder_pan.pos", "right_shoulder_pan.pos"]
        self.obs = {name: float for name in self.names}
        self.obs["top"] = (480, 640, 3)
        self.actions = {name: float for name in self.names}
        self.policy = {
            "input_features": {"observation.state": {"type": "STATE", "shape": [2]},
                               "observation.images.camera1": {"type": "VISUAL", "shape": [3, 480, 640]}},
            "output_features": {"action": {"type": "ACTION", "shape": [2]}},
        }
        self.schema = {"robot_type": "bi_so_follower", "features": {
            "observation.state": {"names": self.names, "shape": [2]},
            "action": {"names": self.names, "shape": [2]},
            "observation.images.top": {"shape": [480, 640, 3]},
        }}
        self.mapping = {"observation.images.top": "observation.images.camera1"}

    def check(self):
        return MODULE.validate_feature_contract(self.policy, self.schema, self.mapping, self.obs, self.actions, "bi_so_follower")

    def test_matching_names_order_and_camera_contract(self):
        self.assertEqual(self.check(), (self.names, self.names))

    def test_rejects_swapped_left_right_actions(self):
        self.actions = dict(reversed(list(self.actions.items())))
        with self.assertRaisesRegex(ValueError, "names/order"):
            self.check()

    def test_rejects_state_vector_dimension_change(self):
        self.policy["input_features"]["observation.state"]["shape"] = [1]
        with self.assertRaisesRegex(ValueError, "dimension"):
            self.check()

    def test_rejects_missing_camera_mapping(self):
        self.mapping = {}
        with self.assertRaisesRegex(ValueError, "camera keys"):
            self.check()

    def test_rejects_incompatible_image_resolution(self):
        self.obs["top"] = (240, 320, 3)
        with self.assertRaisesRegex(ValueError, "shape mismatch"):
            self.check()

    def test_rejects_different_robot_type(self):
        self.schema["robot_type"] = "so101_follower"
        with self.assertRaisesRegex(ValueError, "robot_type"):
            self.check()


class InferenceTargetLimitTests(unittest.TestCase):
    def setUp(self):
        self.args = [
            "--robot.left_arm_config.max_relative_target={shoulder_lift: 10}",
            "--robot.right_arm_config.max_relative_target={shoulder_lift: 10}",
            "--robot.id=dual_follower", "--robot.calibration_dir=existing/calibration",
            "--robot.cameras={top: existing}", "--teleop.type=bi_so_leader",
        ]

    def test_default_keeps_existing_arm_limits(self):
        result = MODULE.inference_hardware_args(self.args)
        self.assertEqual(result, self.args[:-1])

    def test_explicit_disable_replaces_both_limits_and_preserves_other_hardware(self):
        original = self.args.copy()
        result = MODULE.inference_hardware_args(self.args, no_target_limit=True)
        self.assertEqual(self.args, original)
        self.assertEqual(result[:3], self.args[2:5])
        for side in ("left", "right"):
            prefix = f"--robot.{side}_arm_config.max_relative_target="
            self.assertEqual([a for a in result if a.startswith(prefix)], [prefix + "null"])
        self.assertFalse(any(a.startswith("--teleop.") for a in result))


if __name__ == "__main__":
    unittest.main()

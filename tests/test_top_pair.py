"""Paired top images must retain one-frame correspondence without device reads."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("top_pair", ROOT / "src/cuk_robotics/teleoperation/top_pair.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
try:
    import numpy as np
    from PIL import Image
except ImportError:
    np = None


@unittest.skipIf(np is None, "numpy/Pillow unavailable")
class TopPairTests(unittest.TestCase):
    def make_overlay(self, directory):
        rgba = np.zeros((2, 3, 4), dtype=np.uint8)
        rgba[0, 1] = [96, 96, 96, 255]
        rgba[0, 2] = [200, 100, 0, 128]
        path = Path(directory) / "mask.png"
        Image.fromarray(rgba).save(path)
        return MODULE.TopOverlay(path, (2, 3, 3))

    def test_blend_preserves_original_and_handles_transparent_opaque_partial(self):
        with tempfile.TemporaryDirectory() as directory:
            overlay = self.make_overlay(directory)
            raw = np.full((2, 3, 3), 40, dtype=np.uint8)
            original = raw.copy()
            result = overlay.apply(raw)
            np.testing.assert_array_equal(raw, original)
            np.testing.assert_array_equal(result[0, 0], [40, 40, 40])
            np.testing.assert_array_equal(result[0, 1], [96, 96, 96])
            np.testing.assert_array_equal(result[0, 2], [120, 70, 20])
            with self.assertRaises(ValueError):
                overlay.apply(raw.astype(np.float32))
            with self.assertRaises(ValueError):
                MODULE.TopOverlay(overlay.path, (4, 3, 3))

    def test_single_read_and_no_state_action_or_shared_buffer_mutation(self):
        with tempfile.TemporaryDirectory() as directory:
            overlay = self.make_overlay(directory)
            shared = np.full((2, 3, 3), 40, dtype=np.uint8)
            calls = []
            robot = SimpleNamespace(observation_features={"joint.pos": float, "top": shared.shape},
                                    action_features={"joint.pos": float},
                                    get_observation=lambda: calls.append(1) or {"joint.pos": 1.5, "top": shared})
            MODULE.add_top_pair(robot, overlay)
            result = robot.get_observation()
            self.assertEqual(len(calls), 1)
            self.assertEqual(result["joint.pos"], 1.5)
            self.assertEqual(robot.action_features, {"joint.pos": float})
            np.testing.assert_array_equal(result["top_raw"], shared)
            result["top_raw"][:] = 0
            self.assertTrue(np.all(shared == 40))

    def test_factory_restored_on_failure_and_mask_manifest_protected_on_resume(self):
        with tempfile.TemporaryDirectory() as directory:
            overlay = self.make_overlay(directory)
            root = Path(directory) / "dataset"
            def factory(config):
                return SimpleNamespace(observation_features={"top": (2, 3, 3)}, connect=lambda: None,
                                       get_observation=lambda: {"top": np.zeros((2, 3, 3), dtype=np.uint8)})
            official = SimpleNamespace(make_robot_from_config=factory)
            with self.assertRaisesRegex(RuntimeError, "failed"):
                with MODULE.paired_top_recording(official, overlay, root):
                    robot = official.make_robot_from_config(None)
                    root.mkdir()
                    robot.connect()
                    raise RuntimeError("failed")
            self.assertIs(official.make_robot_from_config, factory)
            manifest = json.loads((root / "top_pair.json").read_text())
            self.assertEqual(manifest["overlay_sha256"], sha256((root / "top_overlay.png").read_bytes()).hexdigest())
            with MODULE.paired_top_recording(official, overlay, root, resume=True):
                pass
            (root / "top_overlay.png").write_bytes(b"changed")
            with self.assertRaisesRegex(ValueError, "hash mismatch"):
                with MODULE.paired_top_recording(official, overlay, root, resume=True):
                    pass


if __name__ == "__main__":
    unittest.main()

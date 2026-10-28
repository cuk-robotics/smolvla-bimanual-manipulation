"""Check upload opt-in and session isolation without hardware or network access."""
import importlib.util
import json
import tempfile
from datetime import datetime, timezone
from pathlib import Path
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("recording_options", ROOT / "src/cuk_robotics/teleoperation/recording.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class RecordingOptionsTests(unittest.TestCase):
    def make_saved_dataset(self, directory):
        root = Path(directory)
        (root / "meta").mkdir()
        (root / "data").mkdir()
        (root / "meta/info.json").write_text(json.dumps({"fps": 30, "total_episodes": 22}), encoding="utf-8")
        (root / "data/file-000.parquet").touch()
        return root

    def test_resume_preserves_exact_destination_and_uses_additional_count(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_saved_dataset(directory)
            args, target_root, repo = self.build(resume=True, dataset_root=root,
                                                expected_episodes=22, push_to_hub=True)
            self.assertEqual(repo, "owner/beverage_v1")
            self.assertEqual(target_root, root.resolve())
            self.assertIn("--resume=true", args)
            self.assertIn("--dataset.num_episodes=10", args)
            self.assertIn("--dataset.no_stamp=true", args)
            self.assertEqual(json.loads((root / "meta/info.json").read_text())["total_episodes"], 22)

    def test_resume_rejects_missing_root_wrong_count_fps_and_missing_data(self):
        with self.assertRaisesRegex(ValueError, "existing local"):
            self.build(resume=True)
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_saved_dataset(directory)
            with self.assertRaisesRegex(ValueError, "Expected 21"):
                self.build(resume=True, dataset_root=root, expected_episodes=21)
            with self.assertRaisesRegex(ValueError, "FPS"):
                self.build(resume=True, dataset_root=root, fps=60)
            (root / "data/file-000.parquet").unlink()
            with self.assertRaisesRegex(ValueError, "local data files"):
                self.build(resume=True, dataset_root=root)

    def test_new_recording_rejects_resume_only_parameters(self):
        for options in ({"dataset_root": ROOT}, {"expected_episodes": 22}):
            with self.assertRaisesRegex(ValueError, "requires --resume"):
                self.build(**options)

    def build(self, **options):
        return MODULE.build_recording_args(ROOT, "owner/beverage_v1", "Prepare a beverage.",
                                           episodes=10, episode_seconds=180, reset_seconds=30, **options)

    def test_recording_defaults_to_local_without_upload(self):
        args, root, repo = self.build()
        self.assertIn("--dataset.push_to_hub=false", args)
        self.assertEqual(repo, "owner/beverage_v1")
        self.assertTrue(root.is_relative_to(ROOT / "data" / "lerobot" / repo))
        self.assertIn("--dataset.fps=30", args)

    def test_upload_runs_use_distinct_repo_ids_and_match_local_session(self):
        with patch.object(MODULE, "datetime") as clock:
            clock.now.side_effect = [datetime(2026, 10, 5, 17, 0, 0, 1, tzinfo=timezone.utc),
                                    datetime(2026, 10, 5, 17, 0, 0, 2, tzinfo=timezone.utc)]
            first = self.build(push_to_hub=True)
            second = self.build(push_to_hub=True)
        self.assertNotEqual(first[2], second[2])
        self.assertNotEqual(first[1], second[1])
        for args, root, repo in (first, second):
            self.assertEqual(repo, "owner/beverage_v1_" + root.name)
            self.assertIn("--dataset.push_to_hub=true", args)
            self.assertIn("--dataset.private=false", args)
            self.assertIn("--dataset.no_stamp=true", args)

    def test_private_upload_is_explicit(self):
        args, _, _ = self.build(push_to_hub=True, private=True)
        self.assertIn("--dataset.private=true", args)
        with self.assertRaisesRegex(ValueError, "requires"):
            self.build(private=True)

    def test_rejects_invalid_or_reserved_repo_before_device_dispatch(self):
        for repo in ("missing_owner", "owner/eval_beverage", "owner/" + "x" * 90):
            with self.subTest(repo=repo), self.assertRaises(ValueError):
                MODULE.build_recording_args(ROOT, repo, "Prepare.", episodes=1,
                                           episode_seconds=10, reset_seconds=0, push_to_hub=True)

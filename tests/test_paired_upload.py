"""Two variants, explicit network opt-in, and four-video upload suppression."""
import contextlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from cuk_robotics import paired_upload
import test_top_variants as fixtures


class PairedRepoTests(unittest.TestCase):
    def test_prepare_and_upload_are_mutually_exclusive(self):
        with self.assertRaisesRegex(ValueError, "mutually exclusive"):
            paired_upload.publish_top_variants(ROOT, "owner/check", ROOT / "unused", push_to_hub=True, prepare_only=True)

    def test_two_names_and_suffix_length_validation(self):
        self.assertEqual(paired_upload.paired_repo_ids("owner/session"),
                         {"raw": "owner/session_raw", "masked": "owner/session_masked"})
        self.assertEqual(len(paired_upload.paired_repo_ids("owner/" + "x"*89)["masked"].split("/")[1]), 96)
        for name in ("missing_owner", "owner/", "owner/" + "x"*90):
            with self.assertRaises(ValueError):
                paired_upload.paired_repo_ids(name)


@unittest.skipIf(fixtures.pa is None, "pyarrow unavailable")
class PairedUploadTests(unittest.TestCase):
    def test_prepare_only_exports_and_loads_both_without_any_push(self):
        with tempfile.TemporaryDirectory() as directory:
            source = fixtures.TopVariantTests.make_source(self, directory)
            output = Path(directory) / "exports"
            loaded = []
            def factory(**kwargs):
                loaded.append(kwargs["repo_id"])
                def no_push(**options):
                    raise AssertionError("Preparation must never call the Hub")
                return SimpleNamespace(push_to_hub=no_push)
            result = paired_upload.publish_top_variants(source, "owner/session", output,
                            prepare_only=True, dataset_factory=factory)
            self.assertEqual(loaded, ["owner/session_raw", "owner/session_masked"])
            self.assertEqual({v["status"] for v in result.values()}, {"prepared"})
            self.assertEqual(json.loads((output / "hub_publish.json").read_text()), result)
            for variant in ("raw", "masked"):
                self.assertTrue((output / variant / "meta/info.json").is_file())

    def test_default_only_validates_without_export_or_hub_calls(self):
        with tempfile.TemporaryDirectory() as directory:
            source = fixtures.TopVariantTests.make_source(self, directory)
            output = Path(directory) / "exports"
            def no_factory(**kwargs):
                raise AssertionError("Default validation must never load/upload datasets")
            result = paired_upload.publish_top_variants(source, "owner/session", output, dataset_factory=no_factory)
            self.assertFalse(output.exists())
            self.assertEqual({v["status"] for v in result.values()}, {"planned"})

    def test_both_load_before_upload_and_use_three_cameras_with_safe_public_provenance(self):
        with tempfile.TemporaryDirectory() as directory:
            source = fixtures.TopVariantTests.make_source(self, directory)
            output = Path(directory) / "exports"
            events = []
            def factory(**kwargs):
                root = kwargs["root"]
                repo = kwargs["repo_id"]
                self.assertEqual(kwargs["video_backend"], "pyav")
                info = json.loads((root / "meta/info.json").read_text())
                self.assertEqual(len(info["features"]), 3)
                self.assertNotIn("observation.images.top_raw", info["features"])
                provenance = json.loads((root / "meta/top_variant.json").read_text())
                self.assertNotIn(str(source), json.dumps(provenance))
                self.assertEqual(provenance["top_has_overlay"], repo.endswith("_masked"))
                events.append(("load", repo))
                def push(**options):
                    self.assertTrue(options["private"])
                    self.assertEqual(options["allow_patterns"], ["data/**", "meta/**", "videos/**"])
                    self.assertEqual(sum(e[0]=="load" for e in events), 2)
                    events.append(("push", repo))
                return SimpleNamespace(push_to_hub=push)
            result = paired_upload.publish_top_variants(source, "owner/session", output,
                        push_to_hub=True, private=True, dataset_factory=factory)
            self.assertEqual(events, [("load","owner/session_raw"), ("load","owner/session_masked"),
                                      ("push","owner/session_raw"), ("push","owner/session_masked")])
            self.assertEqual({v["status"] for v in result.values()}, {"uploaded"})
            self.assertEqual(json.loads((output / "hub_publish.json").read_text()), result)

    def test_partial_failure_keeps_first_success_and_both_local_exports(self):
        with tempfile.TemporaryDirectory() as directory:
            source = fixtures.TopVariantTests.make_source(self, directory)
            output = Path(directory) / "exports"
            def factory(**kwargs):
                def push(**options):
                    if kwargs["repo_id"].endswith("_masked"):
                        raise OSError("offline test failure")
                return SimpleNamespace(push_to_hub=push)
            with self.assertRaisesRegex(OSError, "offline test"):
                paired_upload.publish_top_variants(source, "owner/session", output,
                    push_to_hub=True, dataset_factory=factory)
            status = json.loads((output / "hub_publish.json").read_text())
            self.assertEqual(status["raw"]["status"], "uploaded")
            self.assertEqual(status["masked"]["status"], "failed")
            self.assertTrue((output / "raw/meta/info.json").is_file())
            self.assertTrue((output / "masked/meta/info.json").is_file())


@unittest.skipUnless(all(importlib.util.find_spec(name) for name in ("lerobot", "draccus", "yaml")), "Requires LeRobot environment")
class PairedUploadCliTests(unittest.TestCase):
    def test_dispatch_routes_only_paired_uploads_and_validation_never_publishes(self):
        from cuk_robotics.teleoperation import cli, top_pair, rerun_display
        from cuk_robotics.teleoperation import console_logging
        from lerobot.scripts import lerobot_record as official
        for paired, upload, prepare, validate, count in ((True,True,False,False,1), (True,False,False,False,1),
                                               (False,True,False,False,1), (True,True,False,True,1),
                                               (True,True,False,False,0), (True,False,True,False,1),
                                               (True,False,True,True,1)):
            with self.subTest(paired=paired,upload=upload,prepare=prepare,validate=validate,count=count), tempfile.TemporaryDirectory() as directory:
                base = Path(directory)
                captured = {}
                config = SimpleNamespace(display_data=True, display_mode="rerun", dataset=SimpleNamespace(fps=30),
                    robot=SimpleNamespace(cameras={k:SimpleNamespace(fourcc=None) for k in ("left_wrist","right_wrist","top")},
                        left_arm_config=SimpleNamespace(max_relative_target=10),right_arm_config=SimpleNamespace(max_relative_target=10)))
                def parse(**kwargs):
                    captured["args"] = kwargs["args"]
                    return config
                def dispatch():
                    root = Path(next(a.split("=",1)[1] for a in sys.argv if a.startswith("--dataset.root=")))
                    (root / "meta").mkdir(parents=True)
                    (root / "meta/info.json").write_text(json.dumps({"total_episodes":count}))
                args = ["run_robot.py","--project-root",str(base),"record","--repo-id","owner/check",
                        "--task","Check.","--episodes","1","--episode-seconds","1","--reset-seconds","0"]
                if paired: args += ["--top-overlay","mask.png","--raw-top-input"]
                if upload: args += ["--push-to-hub"]
                if prepare: args += ["--prepare-hub"]
                if validate: args += ["--validate-only"]
                with patch.object(sys,"argv",args), patch.object(cli,"BASE",base), \
                     patch.object(cli,"hardware_args",return_value=[]), \
                     patch.object(cli,"camera_profiles",return_value={"top":{"height":2,"width":3}}), \
                     patch.object(cli,"install_camera_layout",return_value=lambda *a:None), \
                     patch.object(cli.draccus,"parse",side_effect=parse), \
                     patch.object(top_pair,"TopOverlay",return_value=SimpleNamespace(sha256="test")), \
                     patch.object(top_pair,"paired_top_recording",return_value=contextlib.nullcontext()), \
                     patch.object(rerun_display,"install_display_logging"), \
                     patch.object(rerun_display,"start_local_viewer",return_value=9876), \
                     patch.object(console_logging,"readable_console",return_value=contextlib.nullcontext()), \
                     patch.object(official,"main",side_effect=dispatch) as main, \
                     patch.object(paired_upload,"publish_top_variants",return_value={"raw":{"repo_id":"owner/check_raw","output":"raw"},"masked":{"repo_id":"owner/check_masked","output":"masked"}}) as publish, \
                     contextlib.redirect_stdout(io.StringIO()):
                    cli.main()
                expected_flag = str(upload and not paired).lower()
                self.assertIn("--dataset.push_to_hub="+expected_flag, captured["args"])
                self.assertEqual(main.call_count, 0 if validate else 1)
                self.assertEqual(publish.call_count, int(paired and (upload or prepare) and not validate and count>0))
                if publish.called:
                    self.assertEqual(publish.call_args.kwargs["push_to_hub"], upload)
                    self.assertEqual(publish.call_args.kwargs["prepare_only"], prepare)
                    self.assertFalse(publish.call_args.kwargs["private"])


if __name__ == "__main__":
    unittest.main()

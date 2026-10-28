"""Exercise Windows port denial and viewer failures without devices or GUI."""
import errno
import importlib.util
from pathlib import Path
import types
import unittest
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("rerun_display", ROOT / "src/cuk_robotics/teleoperation/rerun_display.py")
DISPLAY = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(DISPLAY)


class RerunDisplayTests(unittest.TestCase):
    def test_local_logging_avoids_forced_jpeg_and_only_throttles_display(self):
        original = Mock()
        observation, action = {"left_wrist": object()}, {"joint": 1}
        log = DISPLAY.make_display_logger(original, max_fps=30)
        with patch.object(DISPLAY.time, "perf_counter", side_effect=[0.0, 0.01, 0.04]):
            for _ in range(3):
                log(observation=observation, action=action, compress_images=True)
        self.assertEqual(original.call_count, 2)
        original.assert_called_with(observation=observation, action=action, compress_images=False)
        self.assertEqual(action, {"joint": 1})

    def test_visualization_failure_is_not_hidden(self):
        log = DISPLAY.make_display_logger(Mock(side_effect=RuntimeError("display failed")))
        with self.assertRaisesRegex(RuntimeError, "display failed"):
            log()

    def test_60hz_control_keeps_30hz_display_cadence(self):
        original = Mock()
        log = DISPLAY.make_display_logger(original, max_fps=30)
        with patch.object(DISPLAY.time, "perf_counter", side_effect=[tick / 60 for tick in range(600)]):
            for _ in range(600):
                log()
        self.assertEqual(original.call_count, 300)

    def test_display_resumes_after_stall_without_catch_up(self):
        original = Mock()
        log = DISPLAY.make_display_logger(original, max_fps=30)
        with patch.object(DISPLAY.time, "perf_counter", side_effect=[0.0, 0.5, 0.501, 0.51, 0.534]):
            for _ in range(5):
                log()
        self.assertEqual(original.call_count, 3)

    def test_reserved_default_selects_available_port(self):
        denied = PermissionError(errno.EACCES, "reserved port")
        denied.winerror = 10013
        with patch.object(DISPLAY, "_probe_port", side_effect=[denied, 54321]) as probe:
            self.assertEqual(DISPLAY.select_rerun_port(), 54321)
        self.assertEqual([call.args for call in probe.call_args_list], [(9876,), (0,)])

    def test_busy_default_selects_available_port(self):
        with patch.object(DISPLAY, "_probe_port", side_effect=[OSError(errno.EADDRINUSE, "busy"), 54321]):
            self.assertEqual(DISPLAY.select_rerun_port(), 54321)

    def test_explicit_blocked_port_fails_before_spawning(self):
        rr = types.SimpleNamespace(init=Mock(), RecordingStream=Mock(), spawn=Mock())
        with patch.dict("sys.modules", {"rerun": rr}), patch.object(DISPLAY, "_probe_port", side_effect=PermissionError(errno.EACCES, "denied")):
            with self.assertRaisesRegex(RuntimeError, "9876 is unavailable"):
                DISPLAY.start_local_viewer(9876)
        rr.init.assert_not_called()
        rr.RecordingStream.assert_not_called()
        rr.spawn.assert_not_called()

    def test_unrelated_socket_error_is_not_hidden(self):
        with patch.object(DISPLAY, "_probe_port", side_effect=OSError(errno.EMFILE, "too many sockets")) as probe:
            with self.assertRaises(OSError):
                DISPLAY.select_rerun_port()
        probe.assert_called_once_with(9876)

    def test_viewer_receives_selected_port_and_propagates_failure(self):
        rr = types.SimpleNamespace(init=Mock(), RecordingStream=Mock(), spawn=Mock(side_effect=RuntimeError("viewer failed")))
        with patch.dict("sys.modules", {"rerun": rr}), patch.object(DISPLAY, "select_rerun_port", return_value=54321), patch.dict("os.environ", {"LEROBOT_RERUN_MEMORY_LIMIT": "10%"}):
            with self.assertRaisesRegex(RuntimeError, "viewer failed"):
                DISPLAY.start_local_viewer()
        rr.init.assert_not_called()
        rr.RecordingStream.assert_called_once_with("SO101_display_setup", send_properties=False)
        rr.spawn.assert_called_once_with(port=54321, connect=False, recording=rr.RecordingStream.return_value, memory_limit="10%")

    def test_renderer_override_is_only_applied_during_spawn(self):
        rr = types.SimpleNamespace(RecordingStream=Mock(), spawn=Mock())
        rr.spawn.side_effect = lambda **kwargs: self.assertEqual(DISPLAY.os.environ["WGPU_BACKEND"], "gl")
        with patch.dict("sys.modules", {"rerun": rr}), patch.object(DISPLAY, "select_rerun_port", return_value=54321), patch.dict("os.environ", {"WGPU_BACKEND": "vulkan"}):
            DISPLAY.start_local_viewer(renderer="gl")
            self.assertEqual(DISPLAY.os.environ["WGPU_BACKEND"], "vulkan")

    def test_renderer_environment_restored_after_spawn_failure(self):
        rr = types.SimpleNamespace(RecordingStream=Mock(), spawn=Mock(side_effect=RuntimeError("viewer failed")))
        with patch.dict("sys.modules", {"rerun": rr}), patch.object(DISPLAY, "select_rerun_port", return_value=54321), patch.dict("os.environ", {}, clear=True):
            with self.assertRaisesRegex(RuntimeError, "viewer failed"):
                DISPLAY.start_local_viewer(renderer="gl")
            self.assertNotIn("WGPU_BACKEND", DISPLAY.os.environ)


if __name__ == "__main__":
    unittest.main()

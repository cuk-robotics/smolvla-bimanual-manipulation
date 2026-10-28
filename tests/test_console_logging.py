"""Check recording status and targeted warning throttling without devices."""
import importlib.util
import io
import logging
from pathlib import Path
import sys
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import Mock, patch

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("console_logging", ROOT / "src/cuk_robotics/teleoperation/console_logging.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
MESSAGE = MODULE.TARGET_WARNING + "\n{'wrist_flex': {'original goal_pos': 22.0, 'safe goal_pos': 27.0}}"


def record(message=MESSAGE, level=logging.WARNING, path="C:/env/lerobot/robots/utils.py"):
    return logging.LogRecord("root", level, path, 121, message, (), None)


class ConsoleLoggingTests(unittest.TestCase):
    def setUp(self):
        self.root = logging.getLogger()
        handlers, level = self.root.handlers[:], self.root.level
        self.addCleanup(lambda: setattr(self.root, "handlers", handlers))
        self.addCleanup(lambda: self.root.setLevel(level))
        self.output = io.StringIO()

        def initialize():
            self.root.handlers.clear()
            self.handler = logging.StreamHandler(self.output)
            self.handler.setFormatter(logging.Formatter("%(levelname)s %(message)s"))
            self.root.addHandler(self.handler)
            self.root.setLevel(logging.INFO)

        self.official = SimpleNamespace(init_logging=initialize)
        self.dataset = SimpleNamespace(num_episodes=30, reset_time_s=20)

    def test_rate_limit_counts_all_joints_and_preserves_first_and_latest_detail(self):
        ticks = iter([0, 0.01, 10, 29.99, 30])
        limiter = MODULE.TargetWarningFilter(clock=lambda: next(ticks))
        accepted = [limiter.filter(record()) for _ in range(5)]
        self.assertEqual(accepted, [True, False, False, False, True])
        self.assertEqual((limiter.total, limiter.hidden, limiter.pending), (5, 3, 0))

    def test_resume_banner_counts_saved_plus_additional_episodes(self):
        self.dataset.num_episodes = 8
        with MODULE.readable_console(self.official, dataset=self.dataset, episode_offset=22):
            self.official.init_logging()
            logging.info("Recording episode 22")
        self.assertIn("Episode 23/30 (episode_index=22)", self.output.getvalue())

    def test_other_warnings_errors_and_info_always_pass(self):
        limiter = MODULE.TargetWarningFilter(clock=lambda: 0)
        limiter.filter(record())
        for entry in (record("Camera timed out"), record(level=logging.ERROR),
                      record("Recording episode 0", logging.INFO),
                      record(path="C:/other/utils.py")):
            self.assertTrue(limiter.filter(entry))
        self.assertEqual(limiter.total, 1)

    def test_episode_banners_survive_flood_and_warning_repeats_current_stage(self):
        with MODULE.readable_console(self.official, dataset=self.dataset):
            self.official.init_logging()
            logging.info("Recording episode 0")
            for _ in range(1000):
                self.root.handle(record())
            logging.info("Reset the environment")
            logging.info("Recording episode 1")
            logging.warning("Camera frame is too old")
            logging.error("Motor disconnected")
            logging.info("Re-record episode")
            logging.info("Stop recording")
            logging.info("Exiting")
        output = self.output.getvalue()
        self.assertEqual(output.count(MODULE.TARGET_WARNING), 1)
        self.assertIn("[RECORDING] Episode 1/30 (episode_index=0)", output)
        self.assertIn("[RECORDING] Episode 2/30 (episode_index=1)", output)
        self.assertIn("[RESET]", output)
        self.assertIn("[RE-RECORD]", output)
        self.assertIn("[STOP]", output)
        self.assertIn("[EXIT]", output)
        self.assertIn("Camera frame is too old", output)
        self.assertIn("Motor disconnected", output)
        self.assertIn("1000 messages; 999 hidden", output)
        self.assertIn("protection remains active", output)
        self.assertEqual(self.handler.filters, [])

    def test_verbose_keeps_every_warning_and_cleanup_survives_exception(self):
        original = self.official.init_logging
        with self.assertRaisesRegex(RuntimeError, "test"):
            with MODULE.readable_console(self.official, verbose=True, dataset=self.dataset):
                self.official.init_logging()
                for _ in range(3):
                    self.root.handle(record())
                raise RuntimeError("test")
        self.assertIs(self.official.init_logging, original)
        self.assertEqual(self.output.getvalue().count(MODULE.TARGET_WARNING), 3)
        self.assertEqual(self.handler.formatter._fmt, "%(levelname)s %(message)s")

    def test_file_handler_keeps_every_original_warning(self):
        original = self.official.init_logging
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "test.log"
            file_handler = logging.FileHandler(path, encoding="utf-8")
            def initialize():
                original()
                self.root.addHandler(file_handler)
            self.official.init_logging = initialize
            try:
                with MODULE.readable_console(self.official):
                    self.official.init_logging()
                    for _ in range(5):
                        self.root.handle(record())
                file_handler.flush()
                self.assertEqual(path.read_text(encoding="utf-8").count(MODULE.TARGET_WARNING), 5)
                self.assertEqual(self.output.getvalue().count(MODULE.TARGET_WARNING), 1)
            finally:
                self.root.removeHandler(file_handler)
                file_handler.close()

    @unittest.skipUnless(importlib.util.find_spec("lerobot"), "Requires LeRobot environment")
    def test_filter_attaches_after_real_lerobot_logging_initialization(self):
        from lerobot.scripts import lerobot_record as official
        original = official.init_logging
        with MODULE.readable_console(official, dataset=self.dataset):
            official.init_logging()
            handler = next(h for h in self.root.handlers if isinstance(h, logging.StreamHandler))
            handler.setStream(self.output)
            logging.info("Recording episode 0")
            for _ in range(20):
                self.root.handle(record())
        self.assertIs(official.init_logging, original)
        self.assertEqual(self.output.getvalue().count(MODULE.TARGET_WARNING), 1)
        self.assertIn("20 messages; 19 hidden", self.output.getvalue())
        self.assertIn("[RECORDING] Episode 1/30", self.output.getvalue())

    @unittest.skipUnless(importlib.util.find_spec("lerobot"), "Requires LeRobot environment")
    def test_installed_record_loop_keeps_original_actions_and_relative_protection(self):
        sys.path.insert(0, str(ROOT / "src"))
        from lerobot.scripts import lerobot_record as official
        from lerobot.robots.utils import ensure_safe_goal_position
        from lerobot.teleoperators import Teleoperator
        original_factory = official.make_default_processors
        events = {"exit_early": False}
        robot = Mock()
        robot.get_observation.return_value = {"left_shoulder_lift.pos": -100.79120879120879}
        sent = []

        def send_action(action):
            bounded = ensure_safe_goal_position({"shoulder_lift": (action["left_shoulder_lift.pos"], -100.79120879120879)}, 10.0)
            sent.append(bounded["shoulder_lift"])
            if len(sent) == 3:
                events["exit_early"] = True
            return {"left_shoulder_lift.pos": bounded["shoulder_lift"]}

        robot.send_action.side_effect = send_action
        teleop = Mock(spec=Teleoperator)
        teleop.get_action.return_value = {"left_shoulder_lift.pos": -113.27472527472527}
        dataset = Mock(fps=30)
        dataset.features = {"action": {"dtype": "float32", "shape": (1,), "names": ["left_shoulder_lift.pos"]},
                            "observation.state": {"dtype": "float32", "shape": (1,), "names": ["left_shoulder_lift.pos"]}}
        with patch.object(official, "init_logging", self.official.init_logging), \
                MODULE.readable_console(official, dataset=self.dataset), \
                patch.object(official, "precise_sleep"):
            official.init_logging()
            logging.info("Recording episode 0")
            processors = official.make_default_processors()
            official.record_loop(robot=robot, events=events, fps=30, teleop_action_processor=processors[0],
                                 robot_action_processor=processors[1], robot_observation_processor=processors[2],
                                 dataset=dataset, teleop=teleop, control_time_s=1, single_task="Test.")
        self.assertEqual(len(sent), 3)
        self.assertTrue(all(abs(value - (-110.79120879120879)) < 1e-8 for value in sent))
        self.assertEqual(dataset.add_frame.call_count, 3)
        for entry in dataset.add_frame.call_args_list:
            self.assertAlmostEqual(float(entry.args[0]["action"][0]), -113.27472527472527, places=4)
        self.assertIs(official.make_default_processors, original_factory)
        self.assertEqual(self.output.getvalue().count(MODULE.TARGET_WARNING), 1)
        self.assertIn("[RECORDING] Episode 1/30", self.output.getvalue())


if __name__ == "__main__":
    unittest.main()

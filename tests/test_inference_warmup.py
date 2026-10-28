"""Warmup must finish before hardware setup and restore the official loader."""
import importlib.util
from pathlib import Path
from types import SimpleNamespace
from threading import Event
import unittest
from unittest.mock import Mock

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("inference_warmup", ROOT / "src/cuk_robotics/teleoperation/inference_warmup.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)


class PolicyWarmupTests(unittest.TestCase):
    def test_reuses_loaded_policy_and_warms_before_hardware_setup(self):
        events = []
        policy = object()
        loader = Mock(side_effect=lambda config: events.append("load") or policy)
        context = SimpleNamespace(_load_pretrained_policy=loader)
        warmup = Mock(side_effect=lambda loaded: events.append("warmup"))
        config = object()
        with MODULE.policy_warmup(context, warmup):
            result = context._load_pretrained_policy(config)
            events.append("hardware")
        self.assertIs(result, policy)
        loader.assert_called_once_with(config)
        warmup.assert_called_once_with(policy)
        self.assertEqual(events, ["load", "warmup", "hardware"])
        self.assertIs(context._load_pretrained_policy, loader)

    def test_warmup_failure_or_interrupt_prevents_hardware_and_restores_loader(self):
        for error in (ValueError("invalid action"), KeyboardInterrupt()):
            with self.subTest(error=type(error).__name__):
                loader = Mock(return_value=object())
                context = SimpleNamespace(_load_pretrained_policy=loader)
                hardware = Mock()
                with self.assertRaises(type(error)):
                    with MODULE.policy_warmup(context, Mock(side_effect=error)):
                        context._load_pretrained_policy(object())
                        hardware()
                hardware.assert_not_called()
                self.assertIs(context._load_pretrained_policy, loader)

    def test_official_failure_restores_loader(self):
        loader = Mock()
        context = SimpleNamespace(_load_pretrained_policy=loader)
        with self.assertRaises(RuntimeError):
            with MODULE.policy_warmup(context, Mock()):
                raise RuntimeError("official rollout failed")
        self.assertIs(context._load_pretrained_policy, loader)

    def test_signal_shutdown_blocks_hardware_and_restores_both_hooks(self):
        for cancel_before_load in (False, True):
            with self.subTest(cancel_before_load=cancel_before_load):
                shutdown = Event()
                if cancel_before_load:
                    shutdown.set()
                loader = Mock(return_value=object())
                context = SimpleNamespace(_load_pretrained_policy=loader)
                hardware = Mock()
                def build(config, shutdown_event):
                    context._load_pretrained_policy(config)
                    hardware()
                official = SimpleNamespace(build_rollout_context=build)
                warmup = Mock(side_effect=lambda loaded: shutdown.set())
                with self.assertRaises(KeyboardInterrupt):
                    with MODULE.rollout_warmup(official, context, warmup):
                        official.build_rollout_context(object(), shutdown)
                hardware.assert_not_called()
                self.assertEqual(warmup.call_count, 0 if cancel_before_load else 1)
                self.assertIs(context._load_pretrained_policy, loader)
                self.assertIs(official.build_rollout_context, build)

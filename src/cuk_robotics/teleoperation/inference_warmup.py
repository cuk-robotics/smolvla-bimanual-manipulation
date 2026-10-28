"""Warm the loaded policy before official rollout connects any hardware."""
from contextlib import contextmanager
import time


@contextmanager
def policy_warmup(context, warmup, shutdown_event=None):
    original = context._load_pretrained_policy

    def load(*args, **kwargs):
        policy = original(*args, **kwargs)
        if shutdown_event is not None and shutdown_event.is_set():
            raise KeyboardInterrupt("Rollout cancelled before warmup.")
        warmup(policy)
        if shutdown_event is not None and shutdown_event.is_set():
            raise KeyboardInterrupt("Rollout cancelled during warmup; hardware remains disconnected.")
        return policy

    context._load_pretrained_policy = load
    try:
        yield
    finally:
        context._load_pretrained_policy = original


@contextmanager
def rollout_warmup(official, context, warmup):
    original = official.build_rollout_context

    def build(config, shutdown_event, *args, **kwargs):
        with policy_warmup(context, warmup, shutdown_event):
            return original(config, shutdown_event, *args, **kwargs)

    official.build_rollout_context = build
    try:
        yield
    finally:
        official.build_rollout_context = original


def warm_policy(policy, path, schema, rename_map, task, device):
    import numpy as np
    import torch
    from lerobot.policies import make_pre_post_processors
    from lerobot.rollout.inference.sync import SyncInferenceEngine

    print("Inference warmup: hardware disconnected; generated actions will be discarded.", flush=True)
    policy.to(device).eval()
    pre, post = make_pre_post_processors(
        policy_cfg=policy.config,
        pretrained_path=str(path),
        pretrained_revision=policy.config.pretrained_revision,
        preprocessor_overrides={
            "device_processor": {"device": device},
            "rename_observations_processor": {"rename_map": rename_map},
        },
    )
    features = schema["features"]
    observation = {"observation.state": np.zeros(features["observation.state"]["shape"], dtype=np.float32)}
    observation.update({
        key: np.zeros(feature["shape"], dtype=np.uint8)
        for key, feature in features.items() if key.startswith("observation.images.")
    })
    action_names = features["action"]["names"]
    engine = SyncInferenceEngine(policy, pre, post, features, action_names, task, device, schema["robot_type"])
    target_device = torch.device(device)
    cuda_devices = []
    if target_device.type == "cuda":
        cuda_devices = [target_device.index if target_device.index is not None else torch.cuda.current_device()]
    durations = []
    with torch.random.fork_rng(devices=cuda_devices):
        try:
            for iteration in range(2):
                engine.reset()
                started = time.perf_counter()
                action = engine.get_action(observation)
                if action is None or list(action.shape) != [len(action_names)] or not torch.isfinite(action).all():
                    raise ValueError("Warmup produced an invalid action; hardware connection aborted.")
                durations.append(time.perf_counter() - started)
                print(f"Inference warmup {iteration + 1}/2: {durations[-1]:.3f}s; action discarded.", flush=True)
        finally:
            engine.reset()
    print("Inference warmup complete: policy queues reset; proceeding to official hardware setup.", flush=True)
    return durations

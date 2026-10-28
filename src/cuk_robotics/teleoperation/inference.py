"""Validate local policy/hardware contracts and delegate motion to LeRobot rollout."""
import json
from pathlib import Path
import sys


def inference_hardware_args(hardware_arguments, *, no_target_limit=False):
    args = [a for a in hardware_arguments if not a.startswith("--teleop.")]
    if no_target_limit:
        limit_options = [f"--robot.{side}_arm_config.max_relative_target=" for side in ("left", "right")]
        args = [a for a in args if not any(a.startswith(prefix) for prefix in limit_options)]
        args.extend(prefix + "null" for prefix in limit_options)
    return args


def read_checkpoint_contract(policy_path, dataset_root):
    policy_path = Path(policy_path).resolve()
    dataset_root = Path(dataset_root).resolve()
    for name in ("config.json", "model.safetensors", "policy_preprocessor.json", "policy_postprocessor.json"):
        if not (policy_path / name).is_file():
            raise FileNotFoundError(policy_path / name)
    policy = json.loads((policy_path / "config.json").read_text(encoding="utf-8"))
    schema = json.loads((dataset_root / "meta/info.json").read_text(encoding="utf-8"))
    pre = json.loads((policy_path / "policy_preprocessor.json").read_text(encoding="utf-8"))
    post = json.loads((policy_path / "policy_postprocessor.json").read_text(encoding="utf-8"))
    rename_map = {}
    for step in pre["steps"]:
        if step["registry_name"] == "rename_observations_processor":
            rename_map = step["config"]["rename_map"]
    for pipeline in (pre, post):
        for step in pipeline["steps"]:
            if step.get("state_file") and not (policy_path / step["state_file"]).is_file():
                raise FileNotFoundError(policy_path / step["state_file"])
    return policy_path, policy, schema, rename_map


def validate_feature_contract(policy, schema, rename_map, observation_features, action_features, robot_type):
    if schema["robot_type"] != robot_type:
        raise ValueError("Dataset robot_type differs from the local robot.")
    features = schema["features"]
    state_names = [k for k, v in observation_features.items() if v is float and k.endswith((".pos", ".vel"))]
    action_names = [k for k in action_features if k.endswith((".pos", ".vel"))]
    for key, names, declared in (
        ("observation.state", state_names, policy["input_features"]["observation.state"]),
        ("action", action_names, policy["output_features"]["action"]),
    ):
        if features[key].get("names") != names:
            raise ValueError(f"{key} names/order differ between source metadata and local robot.")
        if list(features[key]["shape"]) != [len(names)] or list(declared["shape"]) != [len(names)]:
            raise ValueError(f"{key} dimension mismatch.")
    saved_action_names = policy.get("action_feature_names")
    if saved_action_names and list(saved_action_names) != action_names:
        raise ValueError("Policy action_feature_names differs from the verified dataset order.")
    cameras = {f"observation.images.{k}": v for k, v in observation_features.items() if isinstance(v, tuple)}
    expected = {k: v for k, v in policy["input_features"].items() if v["type"] == "VISUAL"}
    if {rename_map.get(k, k) for k in cameras} != set(expected):
        raise ValueError("Policy camera keys differ from the mapped hardware cameras.")
    for key, shape in cameras.items():
        target = rename_map.get(key, key)
        if list(features[key]["shape"]) != list(shape):
            raise ValueError(f"Source/hardware image shape mismatch: {key}")
        if list(expected[target]["shape"]) != [shape[2], shape[0], shape[1]]:
            raise ValueError(f"Policy/hardware image shape mismatch: {target}")
    return state_names, action_names


def run_inference(options, hardware_arguments):
    import draccus
    from lerobot.configs import parser
    from lerobot.robots import make_robot_from_config
    from lerobot.scripts import lerobot_rollout as official

    path, policy, schema, rename_map = read_checkpoint_contract(options.policy_path, options.dataset_root)
    fps = options.fps if options.fps is not None else schema["fps"]
    args = inference_hardware_args(hardware_arguments, no_target_limit=options.no_target_limit)
    args.extend([
        "--strategy.type=base", "--inference.type=sync",
        f"--policy.path={path}", f"--policy.device={options.device}",
        f"--device={options.device}", f"--task={options.task}",
        f"--fps={fps}", f"--duration={options.duration_s or 5}",
        f"--return_to_initial_position={str(options.return_to_initial_position).lower()}", "--play_sounds=false",
        "--use_torch_compile=false", "--rename_map=" + json.dumps(rename_map),
    ])
    previous_argv = sys.argv
    try:
        sys.argv = ["lerobot-rollout", *args]
        config = draccus.parse(config_class=official.RolloutConfig, args=parser.filter_path_args("policy", args))
        # Construction reads calibration and feature definitions; connect() is never called here.
        robot = make_robot_from_config(config.robot)
        states, actions = validate_feature_contract(
            policy, schema, rename_map, robot.observation_features, robot.action_features, robot.name,
        )
        if any(not getattr(config.robot, f"{side}_arm_config").use_degrees for side in ("left", "right")):
            raise ValueError("This workflow expects the recorded SO follower defaults: body joints in degrees, grippers in RANGE_0_100.")
        print(f"Policy: {path}", flush=True)
        print(f"Task: {config.task}", flush=True)
        print(f"Cameras: {rename_map}; state/action: {len(states)}/{len(actions)}", flush=True)
        print(f"Rate: {fps} FPS; duration: {config.duration}s; no recording/upload.", flush=True)
        print(f"Return to startup joint positions before disconnect: {config.return_to_initial_position} (includes grippers and Ctrl+C teardown).", flush=True)
        print("Target difference limits:", {side: getattr(config.robot, f"{side}_arm_config").max_relative_target for side in ("left", "right")}, flush=True)
        if options.validate_only:
            print("Validated official rollout configuration and source feature contract. No hardware connected; weights not loaded.")
            return
        from cuk_robotics.teleoperation.rerun_display import start_local_viewer
        port = start_local_viewer(options.rerun_port, renderer=options.rerun_renderer)
        sys.argv.extend(["--display_ip=127.0.0.1", f"--display_port={port}"])
        from lerobot.rollout import context
        from cuk_robotics.teleoperation.inference_warmup import rollout_warmup, warm_policy

        with rollout_warmup(official, context, lambda loaded: warm_policy(
            loaded, path, schema, rename_map, config.task, config.device,
        )):
            official.main()
    finally:
        sys.argv = previous_argv

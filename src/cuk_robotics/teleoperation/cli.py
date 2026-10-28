"""Run official LeRobot commands, with optional camera-only Rerun display.

Robot control, dataset collection and policy rollout remain in installed LeRobot scripts.
This launcher supplies their CLI arguments, display layout and local viewer port.
"""
import argparse
import json
import math
import os
import sys
import time
from pathlib import Path

import draccus
import yaml


BASE = Path(__file__).resolve().parents[3]
if not (BASE / "pyproject.toml").is_file():
    BASE = Path.cwd()
os.environ["PATH"] = str(Path(sys.executable).parent / "Scripts") + os.pathsep + os.environ.get("PATH", "")


def hardware_profile(wrist_fourcc=None, *, include_cameras=True):
    from cuk_robotics.config import load_hardware
    path = BASE / "configs" / "local" / "hardware.json"
    if not path.is_file():
        raise FileNotFoundError("Create configs/local/hardware.json from configs/hardware/so101_bimanual.example.json and configure this machine.")
    return load_hardware(path, BASE, wrist_fourcc=wrist_fourcc, include_cameras=include_cameras)


def camera_profiles(wrist_fourcc=None):
    return hardware_profile(wrist_fourcc)["robot"]["cameras"]


def hardware_args(wrist_fourcc=None, *, include_cameras=True):
    from lerobot.cameras.configs import Cv2Backends

    args = [f"--display_data={str(include_cameras).lower()}", "--display_mode=rerun"]
    for component, settings in hardware_profile(wrist_fourcc, include_cameras=include_cameras).items():
        for key, value in settings.items():
            if key in ("left_arm_config", "right_arm_config"):
                for name, nested in value.items():
                    serialized = yaml.safe_dump(nested, default_flow_style=True, width=10000).strip() if isinstance(nested, dict) else str(nested)
                    args.append(f"--{component}.{key}.{name}={serialized}")
            elif key == "cameras":
                cameras = {}
                for name, profile in value.items():
                    backend = profile.get("backend", 0)
                    backend_name = backend if isinstance(backend, str) else Cv2Backends(backend).name
                    cameras[name] = {**profile, "backend": backend_name}
                args.append(f"--{component}.cameras=" + yaml.safe_dump(cameras, default_flow_style=True, width=10000).strip())
            else:
                args.append(f"--{component}.{key}={value}")
    return args


def install_camera_layout():
    from lerobot.utils import rerun_visualization as visualization
    import rerun.blueprint as blueprint

    original = visualization._build_blueprint

    def build(observation_paths, action_paths, image_paths):
        if not image_paths:
            return original(observation_paths, action_paths, image_paths)
        views = {}
        for name, label in (("left_wrist", "Left wrist"), ("top", "Overall view"), ("right_wrist", "Right wrist")):
            paths = [path for path in image_paths if path.rsplit(".", 1)[-1] == name]
            if len(paths) != 1:
                raise RuntimeError(f"Expected one image for {name}, got {paths}")
            views[name] = blueprint.Spatial2DView(origin=paths[0], name=label)
        layout = blueprint.Vertical(
            blueprint.Horizontal(views["left_wrist"], views["right_wrist"], column_shares=[1, 1]),
            views["top"],
            row_shares=[1, 1],
        )
        return blueprint.Blueprint(layout, auto_layout=False, auto_views=False, collapse_panels=True)

    visualization._build_blueprint = build
    return build


def run_preview(seconds, rerun_port, wrist_fourcc=None):
    from lerobot.cameras.opencv import OpenCVCamera, OpenCVCameraConfig
    from lerobot.utils.rerun_visualization import init_rerun, shutdown_rerun
    from lerobot.utils.visualization_utils import log_visualization_data

    cameras = {}
    try:
        for name, profile in camera_profiles(wrist_fourcc).items():
            options = {key: value for key, value in profile.items() if key != "type"}
            camera = OpenCVCamera(OpenCVCameraConfig(**options))
            camera.connect()
            cameras[name] = camera
        init_rerun(session_name="SO101_three_camera_preview", ip="127.0.0.1", port=rerun_port)
        start = time.perf_counter()
        frames = 0
        while time.perf_counter() - start < seconds:
            log_visualization_data("rerun", observation={name: camera.read_latest() for name, camera in cameras.items()})
            frames += 1
            time.sleep(1 / 30)
        print(f"Three-camera display check: {frames} preview cycles completed. No motor ports opened.", flush=True)
    finally:
        for camera in cameras.values():
            if camera.is_connected:
                camera.disconnect()
        shutdown_rerun()


def main():
    global BASE
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--project-root", type=Path, default=BASE)
    parser.add_argument("mode", choices=("operation", "practice", "record", "preview", "infer"))
    parser.add_argument("--validate-only", action="store_true")
    parser.add_argument("--verbose-target-warnings", action="store_true", help="Print every relative target-limit warning; default prints at most one every 30 seconds")
    parser.add_argument("--rerun-port", type=int, help="Local viewer port; by default use 9876 or an available port if blocked")
    parser.add_argument("--rerun-renderer", choices=("vulkan", "gl"), help="Override the local viewer graphics backend for troubleshooting")
    parser.add_argument("--display-fps", type=int, default=30, help="Target Rerun update rate (default 30); does not change control or recording FPS")
    parser.add_argument("--wrist-fourcc", choices=("MJPG", "YUY2"), help="Wrist-camera USB format; practice defaults to MJPG, other camera modes use the profile; leaves configuration files unchanged")
    parser.add_argument("--fps", type=int, help="Control/data rate; defaults to 60 for operation/practice and 30 for record")
    parser.add_argument("--duration-s", type=float, help="Operation/practice/infer duration; infer defaults to a 5-second trial")
    parser.add_argument("--policy-path", type=Path, help="Local inference checkpoint directory")
    parser.add_argument("--dataset-root", type=Path, help="Existing local dataset for record --resume or inference verification")
    parser.add_argument("--resume", action="store_true", help="Append to the exact --repo-id and existing --dataset-root; --episodes is the additional count")
    parser.add_argument("--expected-episodes", type=int, help="With --resume, refuse to start if the saved episode count differs")
    parser.add_argument("--device", choices=("cuda", "cpu"), default="cuda", help="Inference device")
    parser.add_argument("--no-target-limit", action="store_true", help="Infer only: disable max_relative_target for both arms in this session")
    parser.add_argument("--return-to-initial-position", action="store_true", help="Infer only: return both arms and grippers to the startup joint positions before disconnecting, including after Ctrl+C")
    parser.add_argument("--repo-id", help="Dataset ID; uploads append a unique session timestamp")
    parser.add_argument("--push-to-hub", action="store_true", help="Upload saved record episodes on exit; default is local recording only")
    parser.add_argument("--private", action="store_true", help="Make the new uploaded dataset private; requires record --push-to-hub")
    parser.add_argument("--task")
    parser.add_argument("--episodes", type=int)
    parser.add_argument("--episode-seconds", type=float)
    parser.add_argument("--reset-seconds", type=float)
    parser.add_argument("--preview-seconds", type=float, default=5)
    options = parser.parse_args()
    if options.mode == "practice" and options.wrist_fourcc is None:
        options.wrist_fourcc = "MJPG"
    BASE = options.project_root.resolve()
    if options.resume and (options.mode != "record" or options.dataset_root is None or not options.repo_id or not options.task or options.episodes is None):
        parser.error("--resume requires record, --dataset-root, exact --repo-id, --task and additional --episodes.")
    if options.expected_episodes is not None and (not options.resume or options.expected_episodes < 1):
        parser.error("--expected-episodes requires --resume and a positive count.")
    if options.dataset_root is not None and options.mode != "infer" and not options.resume:
        parser.error("--dataset-root requires infer or record --resume.")
    if options.verbose_target_warnings and options.mode not in ("operation", "practice", "record"):
        parser.error("--verbose-target-warnings is only available for operation/practice/record.")
    if options.rerun_port is not None and not 1 <= options.rerun_port <= 65535:
        parser.error("--rerun-port must be between 1 and 65535.")
    if not 1 <= options.display_fps <= 60:
        parser.error("--display-fps must be between 1 and 60.")
    if options.fps is not None and not 1 <= options.fps <= 120:
        parser.error("--fps must be between 1 and 120.")
    if options.duration_s is not None and (options.mode not in ("operation", "practice", "infer") or not math.isfinite(options.duration_s) or options.duration_s <= 0):
        parser.error("--duration-s must be finite and positive and is only available for operation/practice/infer.")
    if options.mode == "operation":
        if options.wrist_fourcc is not None:
            parser.error("operation does not use cameras; --wrist-fourcc is unavailable.")
        if any(v is not None for v in (options.repo_id, options.task, options.episodes, options.episode_seconds, options.reset_seconds)):
            parser.error("operation does not support dataset recording options.")
    if options.mode == "infer" and (options.policy_path is None or options.dataset_root is None or not options.task or not options.task.strip()):
        parser.error("infer requires --policy-path, --dataset-root and --task.")
    if options.mode == "infer" and any(v is not None for v in (options.repo_id, options.episodes, options.episode_seconds, options.reset_seconds)):
        parser.error("infer uses base rollout without dataset recording options.")
    if options.no_target_limit and options.mode != "infer":
        parser.error("--no-target-limit is only available for infer.")
    if options.return_to_initial_position and options.mode != "infer":
        parser.error("--return-to-initial-position is only available for infer.")
    if options.push_to_hub and options.mode != "record":
        parser.error("--push-to-hub is only available for record.")
    if options.private and not options.push_to_hub:
        parser.error("--private requires record --push-to-hub.")
    if options.wrist_fourcc is not None:
        print(f"Wrist camera USB format override: {options.wrist_fourcc}. Configuration files are unchanged; Rerun still receives raw images.", flush=True)
        if options.mode == "record" and options.wrist_fourcc == "MJPG":
            print("Recording uses decoded MJPG camera images. USB input compression is lossy; check object and tool detail before collecting demonstrations.", flush=True)
    if options.mode != "operation":
        build = install_camera_layout()
        from cuk_robotics.teleoperation.rerun_display import install_display_logging
        install_display_logging(options.display_fps)
    if options.mode == "infer":
        from cuk_robotics.teleoperation.inference import run_inference
        run_inference(options, hardware_args(options.wrist_fourcc))
        return
    if options.mode == "preview":
        if options.validate_only:
            camera_profiles(options.wrist_fourcc)
            build(set(), set(), {f"observation.{name}" for name in camera_profiles()})
            print("Validated preview configuration. No hardware connected.")
            return
        from cuk_robotics.teleoperation.rerun_display import start_local_viewer
        port = start_local_viewer(options.rerun_port, renderer=options.rerun_renderer)
        run_preview(options.preview_seconds, port, options.wrist_fourcc)
        return

    args = hardware_args(options.wrist_fourcc, include_cameras=options.mode != "operation")
    if options.mode in ("operation", "practice"):
        from lerobot.scripts import lerobot_teleoperate as official
        config_class = official.TeleoperateConfig
        args.append(f"--fps={options.fps if options.fps is not None else 60}")
        if options.duration_s is not None:
            args.append(f"--teleop_time_s={options.duration_s}")
    else:
        from lerobot.scripts import lerobot_record as official
        config_class = official.RecordConfig
        settings_path = BASE / "configs" / "recording" / "beverage.json"
        settings = json.loads(settings_path.read_text(encoding="utf-8")) if settings_path.is_file() else {}
        repo = options.repo_id or settings.get("repo_id") or input("Dataset ID (username/dataset_name): ").strip()
        task = options.task or settings.get("single_task") or input("Task description: ").strip()
        episodes = options.episodes if options.episodes is not None else settings.get("num_episodes")
        if episodes is None:
            episodes = int(input("Number of episodes [5]: ") or "5")
        seconds = options.episode_seconds if options.episode_seconds is not None else settings.get("episode_time_s")
        if seconds is None:
            seconds = float(input("Seconds per episode [60]: ") or "60")
        reset_seconds = options.reset_seconds if options.reset_seconds is not None else settings.get("reset_time_s", 30)
        from cuk_robotics.teleoperation.recording import build_recording_args
        record_args, root, target_repo = build_recording_args(
            BASE, repo, task, episodes=episodes, episode_seconds=seconds,
            reset_seconds=reset_seconds, fps=options.fps if options.fps is not None else 30,
            push_to_hub=options.push_to_hub, private=options.private,
            resume=options.resume, dataset_root=options.dataset_root,
            expected_episodes=options.expected_episodes,
        )
        args.extend(record_args)
        print(f"Local dataset output: {root}", flush=True)
        if options.resume:
            import pandas as pd
            tasks = pd.read_parquet(root / "meta" / "tasks.parquet")
            if task not in tasks.index:
                raise ValueError("Resume task must match an existing task in meta/tasks.parquet.")
            saved = json.loads((root / "meta" / "info.json").read_text(encoding="utf-8"))["total_episodes"]
            print(f"Resume: {saved} saved + {episodes} additional = {saved + episodes} planned; next episode_index={saved}.", flush=True)
        upload = ("private" if options.private else "public") if options.push_to_hub else "disabled"
        print(f"Recording: {episodes} episodes; maximum {seconds}s each; reset {reset_seconds}s; {options.fps if options.fps is not None else 30} FPS; upload {upload}.", flush=True)
        if options.push_to_hub:
            print(f"Hub destination on recording exit: https://huggingface.co/datasets/{target_repo}", flush=True)
            print("Resume uses the exact existing Hub ID; new recordings use a separate session ID. Validation does not upload or create a repository.", flush=True)

    config = draccus.parse(config_class=config_class, args=args)
    from cuk_robotics.teleoperation.console_logging import readable_console
    print("Console target-limit warnings: " + ("every message" if options.verbose_target_warnings else "first message, then at most once every 30 seconds") + ". Motor protection is unchanged.", flush=True)
    if options.mode == "operation":
        if config.display_data or config.robot.cameras or any(
            getattr(config.robot, f"{side}_arm_config").cameras for side in ("left", "right")
        ):
            raise ValueError("Operation must have no cameras and display_data=false.")
        print("Operation: 2 leaders + 2 followers; cameras/display/recording disabled.", flush=True)
        print("Rate:", config.fps, flush=True)
        print("Target difference limits:", {side: getattr(config.robot, f"{side}_arm_config").max_relative_target for side in ("left", "right")}, flush=True)
        if options.validate_only:
            print("Validated official operation configuration. No hardware connected.")
            return
        # No display hooks or viewer startup: the official CLI owns motor control.
        sys.argv = ["lerobot-teleoperate", *args]
        with readable_console(official, verbose=options.verbose_target_warnings):
            official.main()
        return
    if options.validate_only:
        if not config.display_data or config.display_mode != "rerun":
            raise ValueError("The three-camera display must be enabled in Rerun mode.")
        build(set(), set(), {f"observation.{name}" for name in camera_profiles()})
        print(f"Validated official {options.mode} configuration and three-camera layout. No hardware connected.")
        print("Cameras:", ", ".join(config.robot.cameras))
        print("Camera USB formats:", {name: camera.fourcc or "auto" for name, camera in config.robot.cameras.items()})
        print("Rate:", config.fps if options.mode == "practice" else config.dataset.fps)
        print(f"Display: raw images; target {options.display_fps} updates/s; renderer={options.rerun_renderer or 'SDK default'}")
        print("Target difference limits:", {side: getattr(config.robot, f"{side}_arm_config").max_relative_target for side in ("left", "right")})
        return
    from cuk_robotics.teleoperation.rerun_display import start_local_viewer
    port = start_local_viewer(options.rerun_port, renderer=options.rerun_renderer)
    args.extend(["--display_ip=127.0.0.1", f"--display_port={port}"])
    # The official CLI entry point still owns the control and recording loops.
    sys.argv = [f"lerobot-{options.mode}", *args]
    with readable_console(official, verbose=options.verbose_target_warnings,
                          dataset=config.dataset if options.mode == "record" else None,
                          episode_offset=saved if options.mode == "record" and options.resume else 0):
        official.main()


if __name__ == "__main__":
    main()

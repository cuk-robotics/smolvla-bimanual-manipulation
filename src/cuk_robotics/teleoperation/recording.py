"""Prepare official recording arguments without importing hardware or Hub clients."""
from datetime import datetime, timedelta, timezone
import json
from pathlib import Path
import re


def build_recording_args(project_root, repo_id, task, *, episodes, episode_seconds,
                         reset_seconds, fps=30, push_to_hub=False, private=False,
                         resume=False, dataset_root=None, expected_episodes=None):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", repo_id):
        raise ValueError("Dataset ID must be username/dataset_name.")
    if repo_id.split("/", 1)[1].startswith("eval_"):
        raise ValueError("The eval_ prefix is reserved for policy evaluation by LeRobot.")
    if not task.strip() or episodes < 1 or episode_seconds <= 0 or reset_seconds < 0:
        raise ValueError("Task must be nonempty; episode count and duration must be positive.")
    if private and not push_to_hub:
        raise ValueError("Private Hub visibility requires --push-to-hub.")
    if not resume and (dataset_root is not None or expected_episodes is not None):
        raise ValueError("Recording --dataset-root/--expected-episodes requires --resume.")
    if resume:
        if dataset_root is None:
            raise ValueError("Resume requires the existing local --dataset-root.")
        root = Path(dataset_root).resolve()
        info = json.loads((root / "meta" / "info.json").read_text(encoding="utf-8"))
        if info.get("fps") != fps:
            raise ValueError("Resume FPS must match the existing dataset.")
        count = info.get("total_episodes")
        if not isinstance(count, int) or count < 1:
            raise ValueError("Resume requires a dataset with saved episodes.")
        if expected_episodes is not None and count != expected_episodes:
            raise ValueError(f"Expected {expected_episodes} saved episodes, found {count}. Recheck the remaining count before resuming.")
        if not any((root / "data").rglob("*.parquet")):
            raise ValueError("Resume requires existing local data files, not metadata alone.")
        target_repo = repo_id
    else:
        stamp = datetime.now(timezone(timedelta(hours=9))).strftime("%Y%m%d_%H%M%S_%f")
        target_repo = f"{repo_id}_{stamp}" if push_to_hub else repo_id
        root = Path(project_root) / "data" / "lerobot" / repo_id / stamp
    if len(target_repo.split("/", 1)[1]) > 96:
        raise ValueError("Dataset name including the session timestamp must be at most 96 characters.")
    args = [
        f"--dataset.repo_id={target_repo}", f"--dataset.single_task={task}", f"--dataset.root={root}",
        f"--dataset.fps={fps}", f"--dataset.num_episodes={episodes}",
        f"--dataset.episode_time_s={episode_seconds}", f"--dataset.reset_time_s={reset_seconds}",
        f"--dataset.push_to_hub={str(push_to_hub).lower()}",
        f"--dataset.private={str(private).lower()}",
        "--dataset.no_stamp=true", "--play_sounds=true",
    ]
    if resume:
        args.append("--resume=true")
    return args, root, target_repo

"""Publish paired top recordings as two standard three-camera datasets."""
import json
from pathlib import Path
import re


def paired_repo_ids(repo_id):
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9_.-]*/[A-Za-z0-9][A-Za-z0-9_.-]*", repo_id):
        raise ValueError("Dataset ID must be username/dataset_name.")
    repos = {variant: f"{repo_id}_{variant}" for variant in ("raw", "masked")}
    if any(len(repo.split("/", 1)[1]) > 96 for repo in repos.values()):
        raise ValueError("Dataset name including session timestamp and _masked must be at most 96 characters.")
    return repos


def publish_top_variants(source, repo_id, output_dir, *, push_to_hub=False, prepare_only=False,
                         private=False, dataset_factory=None):
    """Default is read-only offline validation; uploads require explicit opt-in.

    Both variants must export and load before either upload starts. Hub operations
    are sequential; a local status file records partial success on network errors.
    prepare_only saves both exports with status=prepared and returns before Hub calls.
    """
    from cuk_robotics.top_variants import export_variant

    if push_to_hub and prepare_only:
        raise ValueError("prepare_only and push_to_hub are mutually exclusive.")
    source, output_dir = Path(source).resolve(), Path(output_dir).resolve()
    repos = paired_repo_ids(repo_id)
    if output_dir.exists():
        raise FileExistsError(f"Output exists; choose a new export directory: {output_dir}")
    results = {}
    for variant in repos:
        results[variant] = {**export_variant(source, output_dir / variant, variant, validate_only=True),
                            "repo_id": repos[variant], "status": "planned"}
    if not push_to_hub and not prepare_only:
        return results
    if dataset_factory is None:
        from lerobot.datasets.lerobot_dataset import LeRobotDataset
        dataset_factory = LeRobotDataset

    datasets = {}
    for variant in repos:
        root = output_dir / variant
        export_variant(source, root, variant)
        source_info = json.loads((root / "meta/info.json").read_text(encoding="utf-8"))
        local_provenance = json.loads((root / "top_variant.json").read_text(encoding="utf-8"))
        # Public provenance deliberately excludes machine-local absolute paths.
        public_provenance = {
            "variant": variant,
            "top_has_overlay": variant == "masked",
            "paired_datasets": repos,
            "total_episodes": source_info["total_episodes"],
            "total_frames": source_info["total_frames"],
            "overlay_sha256": local_provenance["source_manifest"]["overlay_sha256"],
            "same_source_episodes_and_actions": True,
            "video_reencoded": False,
        }
        (root / "meta/top_variant.json").write_text(json.dumps(public_provenance, indent=2) + "\n", encoding="utf-8")
        datasets[variant] = dataset_factory(repo_id=repos[variant], root=root, video_backend="pyav")
        results[variant]["status"] = "prepared"

    status_path = output_dir / "hub_publish.json"

    def save_status():
        status_path.write_text(json.dumps(results, indent=2) + "\n", encoding="utf-8")

    save_status()
    if prepare_only:
        return results
    for variant, dataset in datasets.items():
        try:
            dataset.push_to_hub(
                private=private,
                tags=["lerobot", "paired-top", f"top-{variant}"],
                allow_patterns=["data/**", "meta/**", "videos/**"],
            )
        except Exception:
            results[variant]["status"] = "failed"
            save_status()
            raise
        results[variant]["status"] = "uploaded"
        save_status()
    return results

"""Export one paired top stream as standard three-camera LeRobot v3 data.

No decoding/encoding: data parquet and selected video bytes are copied unchanged.
Only the selected top stream's feature, statistics and episode video references change.
"""
from copy import deepcopy
from hashlib import file_digest
import json
from pathlib import Path
import shutil


TOP = "observation.images.top"
RAW = "observation.images.top_raw"
WRISTS = {"observation.images.left_wrist", "observation.images.right_wrist"}
VIDEO_PATH = "videos/{video_key}/chunk-{chunk_index:03d}/file-{file_index:03d}.mp4"


def digest(path):
    with Path(path).open("rb") as file:
        return file_digest(file, "sha256").hexdigest()


def export_variant(source, output, variant, *, validate_only=False):
    import pyarrow.parquet as pq

    source, output = Path(source).resolve(), Path(output).resolve()
    if variant not in ("raw", "masked"):
        raise ValueError("Variant must be raw or masked.")
    if source == output or source in output.parents or output in source.parents:
        raise ValueError("Source and output must be separate directory trees.")
    if output.exists():
        raise FileExistsError(f"Output exists; will not overwrite: {output}")
    info = json.loads((source / "meta/info.json").read_text(encoding="utf-8"))
    manifest = json.loads((source / "top_pair.json").read_text(encoding="utf-8"))
    if manifest.get("version") != 1 or manifest.get("raw_feature") != RAW or manifest.get("masked_feature") != TOP:
        raise ValueError("Unsupported paired-top manifest.")
    if digest(source / "top_overlay.png") != manifest["overlay_sha256"]:
        raise ValueError("Overlay hash mismatch.")
    if info["codebase_version"] != "v3.0" or info["video_path"] != VIDEO_PATH:
        raise ValueError("Only the installed LeRobot v3 video layout is supported.")
    videos = {k for k, value in info["features"].items() if value["dtype"] == "video"}
    if videos != WRISTS | {TOP, RAW}:
        raise ValueError(f"Expected wrist cameras and paired top streams, got {videos}")
    if info["features"][TOP]["shape"] != info["features"][RAW]["shape"]:
        raise ValueError("Paired top dimensions differ.")
    if info["total_episodes"] < 1 or info["total_frames"] < 1:
        raise ValueError("Dataset has no finalized episodes.")
    selected = RAW if variant == "raw" else TOP
    dropped = TOP if variant == "raw" else RAW
    stats = json.loads((source / "meta/stats.json").read_text(encoding="utf-8"))
    if selected not in stats:
        raise ValueError("Selected top statistics are missing.")
    episode_files = sorted((source / "meta/episodes").rglob("*.parquet"))
    if not episode_files:
        raise ValueError("Episode metadata is missing.")
    tables = [(path, pq.read_table(path)) for path in episode_files]
    rows = [row for _, table in tables for row in table.to_pylist()]
    if sorted(row["episode_index"] for row in rows) != list(range(info["total_episodes"])):
        raise ValueError("Episode indices/count differ from finalized metadata.")
    if sum(row["length"] for row in rows) != info["total_frames"]:
        raise ValueError("Episode lengths differ from total_frames.")
    data_files = sorted((source / "data").rglob("*.parquet"))
    if sum(pq.read_metadata(p).num_rows for p in data_files) != info["total_frames"]:
        raise ValueError("Data rows differ from total_frames; finish recording first.")
    copies = {(path, path.relative_to(source)) for path in data_files}
    copies.add((source / "meta/tasks.parquet", Path("meta/tasks.parquet")))
    for row in rows:
        for key in WRISTS | {selected}:
            prefix = f"videos/{key}/"
            chunk, file = row[prefix + "chunk_index"], row[prefix + "file_index"]
            relative = Path(VIDEO_PATH.format(video_key=key, chunk_index=chunk, file_index=file))
            target = Path(VIDEO_PATH.format(video_key=TOP if key == selected else key,
                                            chunk_index=chunk, file_index=file))
            copies.add((source / relative, target))
    for path, _ in copies:
        if not path.is_file():
            raise FileNotFoundError(path)
    report = {"variant": variant, "episodes": info["total_episodes"], "frames": info["total_frames"],
              "video_keys": sorted(WRISTS | {TOP}), "output": str(output)}
    if validate_only:
        return report

    output.mkdir(parents=True)
    incomplete = output / "EXPORT_INCOMPLETE"
    incomplete.write_text("Do not use until export completes successfully.\n", encoding="utf-8")
    hashes = {}
    for path, relative in sorted(copies, key=lambda pair: str(pair[1])):
        target = output / relative
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)
        expected = digest(path)
        if digest(target) != expected:
            raise OSError(f"Copy checksum mismatch: {relative}")
        hashes[relative.as_posix()] = expected
    new_info = deepcopy(info)
    new_info["features"][TOP] = deepcopy(info["features"][selected])
    del new_info["features"][RAW]
    new_stats = deepcopy(stats)
    new_stats[TOP] = deepcopy(stats[selected])
    del new_stats[RAW]
    for name, content in (("info.json", new_info), ("stats.json", new_stats)):
        (output / "meta" / name).write_text(json.dumps(content, indent=2) + "\n", encoding="utf-8")
    for path, table in tables:
        names, columns = [], []
        for name in table.column_names:
            if name.startswith((f"videos/{dropped}/", f"stats/{dropped}/")):
                continue
            renamed = name
            for prefix in ("videos", "stats"):
                if name.startswith(f"{prefix}/{selected}/"):
                    renamed = f"{prefix}/{TOP}/" + name[len(f"{prefix}/{selected}/"):]
            names.append(renamed)
            columns.append(name)
        target = output / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        pq.write_table(table.select(columns).rename_columns(names).replace_schema_metadata(None), target)
    provenance = {**report, "source": str(source), "source_manifest": manifest,
                  "copied_file_sha256": hashes,
                  "note": "Same episodes/actions/split candidates; top video selected without re-encoding."}
    (output / "top_variant.json").write_text(json.dumps(provenance, indent=2) + "\n", encoding="utf-8")
    incomplete.unlink()
    return report

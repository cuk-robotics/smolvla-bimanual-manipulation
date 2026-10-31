"""Check paired stream selection, metadata references and source preservation."""
from hashlib import sha256
import importlib.util
import json
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("top_variants", ROOT / "src/cuk_robotics/top_variants.py")
MODULE = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(MODULE)
try:
    import pyarrow as pa
    import pyarrow.parquet as pq
except ImportError:
    pa = None


@unittest.skipIf(pa is None, "pyarrow unavailable")
class TopVariantTests(unittest.TestCase):
    def make_source(self, directory):
        root = Path(directory) / "source"
        (root / "meta/episodes/chunk-000").mkdir(parents=True)
        (root / "data/chunk-000").mkdir(parents=True)
        features = {k: {"dtype": "video", "shape": [2, 3, 3]} for k in MODULE.WRISTS | {MODULE.TOP, MODULE.RAW}}
        info = {"codebase_version": "v3.0", "video_path": MODULE.VIDEO_PATH, "features": features,
                "total_episodes": 1, "total_frames": 2}
        (root / "meta/info.json").write_text(json.dumps(info))
        (root / "meta/stats.json").write_text(json.dumps({k: {"mean": [i]} for i,k in enumerate(sorted(features))}))
        (root / "top_overlay.png").write_bytes(b"mask fixture")
        (root / "top_pair.json").write_text(json.dumps({"version": 1, "raw_feature": MODULE.RAW,
            "masked_feature": MODULE.TOP, "overlay_sha256": sha256(b"mask fixture").hexdigest()}))
        pq.write_table(pa.table({"episode_index": [0, 0], "frame_index": [0, 1],
                                 "action": [[1.0], [2.0]], "timestamp": [0.0, 1/30]}), root / "data/chunk-000/file-000.parquet")
        pq.write_table(pa.table({"task_index": [0], "task": ["test"]}), root / "meta/tasks.parquet")
        row = {"episode_index": [0], "length": [2]}
        for i,key in enumerate(sorted(features)):
            # Deliberately different video chunks and timestamps for each stream.
            for suffix,value in (("chunk_index", i), ("file_index", i+1),
                                  ("from_timestamp", float(i)), ("to_timestamp", i+2/30)):
                row[f"videos/{key}/{suffix}"] = [value]
            row[f"stats/{key}/mean"] = [[float(i)]]
            video = root / MODULE.VIDEO_PATH.format(video_key=key, chunk_index=i, file_index=i+1)
            video.parent.mkdir(parents=True)
            video.write_bytes(key.encode())
        pq.write_table(pa.table(row), root / "meta/episodes/chunk-000/file-000.parquet")
        return root

    def test_exports_keep_data_and_selected_video_bytes_and_map_episode_references(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_source(directory)
            before = {p.relative_to(root): MODULE.digest(p) for p in root.rglob("*") if p.is_file()}
            for variant in ("raw", "masked"):
                out = Path(directory) / variant
                MODULE.export_variant(root, out, variant, validate_only=True)
                self.assertFalse(out.exists())
                MODULE.export_variant(root, out, variant)
                selected = MODULE.RAW if variant == "raw" else MODULE.TOP
                info = json.loads((out / "meta/info.json").read_text())
                self.assertNotIn(MODULE.RAW, info["features"])
                old = pq.read_table(root / "meta/episodes/chunk-000/file-000.parquet").to_pylist()[0]
                new = pq.read_table(out / "meta/episodes/chunk-000/file-000.parquet").to_pylist()[0]
                self.assertFalse(any(MODULE.RAW in key for key in new))
                for suffix in ("chunk_index", "file_index", "from_timestamp", "to_timestamp"):
                    self.assertEqual(old[f"videos/{selected}/{suffix}"], new[f"videos/{MODULE.TOP}/{suffix}"])
                self.assertEqual(old[f"stats/{selected}/mean"], new[f"stats/{MODULE.TOP}/mean"])
                path = next((out / "videos" / MODULE.TOP).rglob("*.mp4"))
                self.assertEqual(path.read_bytes(), selected.encode())
                self.assertEqual(MODULE.digest(root / "data/chunk-000/file-000.parquet"),
                                 MODULE.digest(out / "data/chunk-000/file-000.parquet"))
            self.assertEqual(before, {p.relative_to(root): MODULE.digest(p) for p in root.rglob("*") if p.is_file()})

    def test_rejects_overwrite_nested_output_and_unfinished_source(self):
        with tempfile.TemporaryDirectory() as directory:
            root = self.make_source(directory)
            for path in (root, root / "nested", root.parent):
                with self.assertRaises(ValueError):
                    MODULE.export_variant(root, path, "raw")
            out = Path(directory) / "exists"
            out.mkdir()
            with self.assertRaises(FileExistsError):
                MODULE.export_variant(root, out, "raw")
            info_path = root / "meta/info.json"
            info = json.loads(info_path.read_text())
            info["total_frames"] = 3
            info_path.write_text(json.dumps(info))
            with self.assertRaisesRegex(ValueError, "total_frames"):
                MODULE.export_variant(root, Path(directory) / "new", "masked")


if __name__ == "__main__":
    unittest.main()

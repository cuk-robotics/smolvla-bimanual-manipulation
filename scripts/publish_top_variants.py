"""Validate or explicitly upload two top variants from a completed local recording."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cuk_robotics.paired_upload import publish_top_variants


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--repo-id", required=True, help="Base ID; the uploads append _raw and _masked")
    parser.add_argument("--output-dir", type=Path, required=True, help="New local directory for both exports")
    parser.add_argument("--push-to-hub", action="store_true", help="Explicitly prepare and upload both datasets; default validates unless --prepare-only is set")
    parser.add_argument("--prepare-only", action="store_true", help="Prepare and load both local exports, then stop before any Hub API call")
    parser.add_argument("--private", action="store_true", help="Create both Hub repositories as private")
    options = parser.parse_args()
    if options.prepare_only and options.push_to_hub:
        parser.error("--prepare-only and --push-to-hub are mutually exclusive.")
    print(json.dumps(publish_top_variants(options.source, options.repo_id, options.output_dir,
                                        push_to_hub=options.push_to_hub, prepare_only=options.prepare_only,
                                        private=options.private), indent=2))


if __name__ == "__main__":
    main()

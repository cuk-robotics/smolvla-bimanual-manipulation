"""Create a new raw/masked three-camera dataset, without changing the source."""
import argparse
import json
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cuk_robotics.top_variants import export_variant


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--variant", choices=("raw", "masked"), required=True)
    parser.add_argument("--validate-only", action="store_true")
    options = parser.parse_args()
    print(json.dumps(export_variant(options.source, options.output, options.variant,
                                    validate_only=options.validate_only), indent=2))


if __name__ == "__main__":
    main()

"""Repository entry point for camera-only browser preview."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
from cuk_robotics.cameras.preview import entrypoint
if __name__ == "__main__":
    entrypoint()

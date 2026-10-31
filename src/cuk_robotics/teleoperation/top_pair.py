"""Derive two top views from one observation; LeRobot owns all episode writing."""
from contextlib import contextmanager
from hashlib import sha256
from io import BytesIO
import json
from pathlib import Path


class TopOverlay:
    def __init__(self, path, shape):
        import numpy as np
        from PIL import Image

        self.path = Path(path).resolve()
        self.content = self.path.read_bytes()
        self.sha256 = sha256(self.content).hexdigest()
        with Image.open(BytesIO(self.content)) as image:
            if image.mode != "RGBA":
                raise ValueError("Top overlay must be an RGBA image with transparency.")
            self.rgba = np.array(image)
        self.shape = tuple(shape)
        if self.rgba.shape != (*self.shape[:2], 4):
            raise ValueError(f"Overlay size {self.rgba.shape} does not match top {self.shape}.")
        if not (np.any(self.rgba[:, :, 3] == 0) and np.any(self.rgba[:, :, 3] > 0)):
            raise ValueError("Overlay must have both transparent and covered pixels.")
        self.opaque = self.rgba[:, :, 3] == 255
        self.partial = (self.rgba[:, :, 3] > 0) & ~self.opaque

    def apply(self, raw):
        import numpy as np

        if raw.shape != self.shape or raw.dtype != np.uint8:
            raise ValueError(f"Expected uint8 RGB top frame {self.shape}, got {raw.shape}/{raw.dtype}.")
        # Do not modify the camera's shared frame buffer.
        result = raw.copy()
        result[self.opaque] = self.rgba[:, :, :3][self.opaque]
        if np.any(self.partial):
            alpha = self.rgba[:, :, 3][self.partial, None].astype(np.uint32)
            rgb = self.rgba[:, :, :3][self.partial].astype(np.uint32)
            result[self.partial] = ((raw[self.partial].astype(np.uint32) * (255 - alpha)
                                     + rgb * alpha + 127) // 255).astype(np.uint8)
        return result


def add_top_pair(robot, overlay):
    """Adapt this robot instance only. No second camera read or motor changes."""
    if "top_raw" in robot.observation_features:
        raise ValueError("top_raw already exists.")
    if tuple(robot.observation_features.get("top", ())) != overlay.shape:
        raise ValueError("Robot top feature does not match the overlay.")
    original = robot.get_observation
    robot.observation_features = {**robot.observation_features, "top_raw": overlay.shape}

    def observation():
        result = dict(original())
        raw = result["top"].copy()
        result["top_raw"] = raw
        result["top"] = overlay.apply(raw)
        return result

    robot.get_observation = observation
    return robot


@contextmanager
def paired_top_recording(official, overlay, root, *, resume=False):
    """Scope the factory adapter and save the exact mask before device connection."""
    original = official.make_robot_from_config
    root = Path(root)
    manifest_path = root / "top_pair.json"
    manifest = {
        "version": 1,
        "raw_feature": "observation.images.top_raw",
        "masked_feature": "observation.images.top",
        "overlay_file": "top_overlay.png",
        "overlay_sha256": overlay.sha256,
        "shape": list(overlay.shape),
        "input_requirement": "OBS virtual camera must output the unmasked scene.",
        "compositing": "uint8 RGB alpha blend, integer round to nearest",
    }
    if resume:
        if not manifest_path.is_file() or json.loads(manifest_path.read_text(encoding="utf-8")) != manifest:
            raise ValueError("Resume requires the same paired-top schema and overlay as the saved session.")
        if sha256((root / "top_overlay.png").read_bytes()).hexdigest() != overlay.sha256:
            raise ValueError("Saved top overlay hash mismatch.")

    def factory(config):
        robot = add_top_pair(original(config), overlay)
        # Official LeRobot creates the dataset directory after the factory call.
        # Save at connect(), after dataset creation, before follower motors connect.
        connect = robot.connect

        def connect_with_provenance(*args, **kwargs):
            if not resume:
                with (root / "top_overlay.png").open("xb") as file:
                    file.write(overlay.content)
                with manifest_path.open("x", encoding="utf-8") as file:
                    json.dump(manifest, file, indent=2)
                    file.write("\n")
            return connect(*args, **kwargs)

        robot.connect = connect_with_provenance
        return robot

    official.make_robot_from_config = factory
    try:
        yield
    finally:
        official.make_robot_from_config = original

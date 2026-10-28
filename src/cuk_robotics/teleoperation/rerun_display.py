"""Prepare a local Rerun viewer without opening cameras or motor ports."""
import errno
import os
import socket
import time


def make_display_logger(original, max_fps=30):
    """Keep local camera images uncompressed and bound only display updates."""
    if max_fps <= 0:
        raise ValueError("Display FPS must be positive.")
    period = 1 / max_fps
    next_update = None

    def log(observation=None, action=None, compress_images=False):
        nonlocal next_update
        now = time.perf_counter()
        # Keep a fixed cadence instead of restarting the interval at each call.
        # At 60 Hz, jitter/roundoff around the 30 Hz boundary otherwise skips
        # an extra control tick and makes camera motion look discontinuous.
        if next_update is not None and now + 1e-9 < next_update:
            return
        # LeRobot forces JPEG for explicit display_ip/display_port. The local
        # viewer on this machine hangs on those images; raw preview works.
        original(observation=observation, action=action, compress_images=False)
        next_update = now + period if next_update is None else next_update + period
        # After a long stall, resume from now rather than sending catch-up frames.
        if next_update <= now + 1e-9:
            next_update = now + period

    log._cuk_original_log = original
    return log


def install_display_logging(max_fps=30):
    """Customize the visualization callback; official motor/data loops stay intact."""
    from lerobot.utils import visualization_utils as visualization

    current = visualization.log_rerun_data
    original = getattr(current, "_cuk_original_log", current)
    visualization.log_rerun_data = make_display_logger(original, max_fps)


def _probe_port(port):
    # Match the viewer's wildcard bind; an exclusive probe also detects listeners
    # on Windows. Port 0 asks the OS for an available, non-excluded port.
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as probe:
        if hasattr(socket, "SO_EXCLUSIVEADDRUSE"):
            probe.setsockopt(socket.SOL_SOCKET, socket.SO_EXCLUSIVEADDRUSE, 1)
        probe.bind(("0.0.0.0", port))
        return probe.getsockname()[1]


def select_rerun_port(requested_port=None):
    """Prefer 9876; fall back only for access-denied/address-in-use errors."""
    if requested_port is not None and not 1 <= requested_port <= 65535:
        raise ValueError("Rerun port must be between 1 and 65535.")
    preferred = 9876 if requested_port is None else requested_port
    try:
        return _probe_port(preferred)
    except OSError as error:
        unavailable = error.errno in (errno.EACCES, errno.EADDRINUSE) or getattr(error, "winerror", None) in (10013, 10048)
        if not unavailable:
            raise
        if requested_port is not None:
            raise RuntimeError(f"Rerun port {preferred} is unavailable: {error}. Omit --rerun-port to select an available port.") from error
        print(f"Rerun default port {preferred} is unavailable: {error}. Selecting another port.", flush=True)
        return _probe_port(0)


def start_local_viewer(requested_port=None, *, renderer=None):
    """Spawn using the public SDK; LeRobot initializes and connects its session."""
    import rerun as rr

    if renderer not in (None, "vulkan", "gl"):
        raise ValueError("Rerun renderer must be vulkan or gl.")
    port = select_rerun_port(requested_port)
    # The probe is closed before spawn, so a concurrent bind can still fail.
    # rr.spawn waits for viewer readiness; propagate failure before robot control.
    # Do not replace the global LeRobot recording with an unused setup session.
    # Suppress setup properties because this stream is only used to spawn a viewer.
    setup = rr.RecordingStream("SO101_display_setup", send_properties=False)
    previous_backend = os.environ.get("WGPU_BACKEND")
    try:
        if renderer is not None:
            os.environ["WGPU_BACKEND"] = renderer
        rr.spawn(port=port, connect=False, recording=setup, memory_limit=os.getenv("LEROBOT_RERUN_MEMORY_LIMIT", "10%"))
    finally:
        if renderer is not None:
            if previous_backend is None:
                os.environ.pop("WGPU_BACKEND", None)
            else:
                os.environ["WGPU_BACKEND"] = previous_backend
    if renderer is not None:
        print(f"Rerun graphics backend: {renderer}", flush=True)
    print(f"Rerun viewer: rerun+http://127.0.0.1:{port}/proxy", flush=True)
    return port

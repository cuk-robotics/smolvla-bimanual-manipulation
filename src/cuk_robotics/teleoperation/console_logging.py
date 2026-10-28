"""Keep episode status readable without changing official control or recording."""
from contextlib import contextmanager
import logging
import re
import time


TARGET_WARNING = "Relative goal position magnitude had to be clamped to be safe."


def is_target_warning(record):
    return (
        record.levelno == logging.WARNING
        and record.pathname.replace("\\", "/").endswith("/lerobot/robots/utils.py")
        and record.getMessage().startswith(TARGET_WARNING + "\n")
    )


class TargetWarningFilter(logging.Filter):
    """Rate-limit only the known safety message, only on the console handler."""
    def __init__(self, interval=30.0, clock=time.monotonic):
        super().__init__()
        self.interval = interval
        self.clock = clock
        self.last_display = None
        self.total = 0
        self.hidden = 0
        self.pending = 0

    def filter(self, record):
        if not is_target_warning(record):
            return True
        self.total += 1
        now = self.clock()
        if self.last_display is not None and now - self.last_display < self.interval:
            self.hidden += 1
            self.pending += 1
            return False
        record.cuk_hidden_target_warnings = self.pending
        self.pending = 0
        self.last_display = now
        return True


class RecordingFormatter(logging.Formatter):
    def __init__(self, original, *, dataset=None, episode_offset=0):
        super().__init__()
        self.original = original or logging.Formatter("%(message)s")
        self.dataset = dataset
        self.episode_offset = episode_offset
        self.stage = None

    def format(self, record):
        text = self.original.format(record)
        message = record.getMessage()
        if self.dataset is not None and record.levelno == logging.INFO:
            episode = re.fullmatch(r"Recording episode (\d+)", message)
            if episode:
                index = int(episode.group(1))
                self.stage = (f"[RECORDING] Episode {index + 1}/{self.episode_offset + self.dataset.num_episodes} "
                              f"(episode_index={index})")
            elif message == "Reset the environment":
                self.stage = f"[RESET] Reposition objects and arms ({self.dataset.reset_time_s}s)"
            elif message == "Re-record episode":
                self.stage = "[RE-RECORD] Repeat the current episode"
            elif message == "Stop recording":
                self.stage = "[STOP] Recording stopped"
            elif message == "Exiting":
                self.stage = "[EXIT] Exiting"
            else:
                return text
            return f"\n{'=' * 64}\n{self.stage}\n{text}\n{'=' * 64}\n"
        if is_target_warning(record):
            hidden = getattr(record, "cuk_hidden_target_warnings", 0)
            text += f"\n[Console] {hidden} repeated target-limit warnings hidden since last display; protection remains active."
            if self.stage:
                text += f"\n{self.stage}"
        return text


@contextmanager
def readable_console(official, *, verbose=False, dataset=None, episode_offset=0):
    """Attach after LeRobot initializes/clears handlers; restore hooks on exit."""
    original_init = official.init_logging
    attached = []

    def init_logging(*args, **kwargs):
        result = original_init(*args, **kwargs)
        for handler in logging.getLogger().handlers:
            if not isinstance(handler, logging.StreamHandler) or isinstance(handler, logging.FileHandler):
                continue
            original_formatter = handler.formatter
            limiter = None if verbose else TargetWarningFilter()
            if limiter is not None:
                handler.addFilter(limiter)
            handler.setFormatter(RecordingFormatter(original_formatter, dataset=dataset, episode_offset=episode_offset))
            attached.append((handler, original_formatter, limiter))
        return result

    official.init_logging = init_logging
    try:
        yield
    finally:
        official.init_logging = original_init
        for handler, formatter, limiter in attached:
            if limiter is not None:
                if limiter.hidden:
                    summary = logging.LogRecord(
                        __name__, logging.INFO, __file__, 0,
                        "Target-limit warning summary: %d messages; %d hidden on console. "
                        "Control protection was unchanged. Use --verbose-target-warnings for every message.",
                        (limiter.total, limiter.hidden), None,
                    )
                    if handler.level <= summary.levelno:
                        handler.handle(summary)
                handler.removeFilter(limiter)
            handler.setFormatter(formatter)

from __future__ import annotations
import logging
import os


class KeyValueFormatter(logging.Formatter):
    """key=value log line formatter (lightweight structured logging)."""

    default_time_format = "%Y-%m-%dT%H:%M:%S"
    default_msec_format = "%s.%03d"

    def format(self, record: logging.LogRecord) -> str:  # noqa: D401
        base = [
            f"ts={self.formatTime(record, self.datefmt)}",
            f"level={record.levelname}",
            f"logger={record.name}",
            f"msg={self._escape(record.getMessage())}",
        ]
        for k, v in sorted(record.__dict__.items()):
            if k.startswith("_"):
                continue
            if k in {"name","msg","args","levelname","levelno","pathname","filename","module","exc_info","exc_text","stack_info","lineno","funcName","created","msecs","relativeCreated","thread","threadName","processName","process"}:
                continue
            base.append(f"{k}={self._escape(v)}")
        if record.exc_info:
            base.append("exc=1")
        return " ".join(base)

    @staticmethod
    def _escape(val) -> str:
        s = str(val)
        if any(ch.isspace() for ch in s):
            s = s.replace('"', "'")
            return f'"{s}"'
        return s


def configure_logging(level: str, *, force: bool = True):
    lvl = getattr(logging, level.upper(), logging.INFO)
    root = logging.getLogger()
    if force:
        for h in list(root.handlers):
            root.removeHandler(h)
    handler = logging.StreamHandler()
    handler.setFormatter(KeyValueFormatter())
    root.addHandler(handler)
    root.setLevel(lvl)
    logging.getLogger("mido").setLevel(max(lvl, logging.WARNING))
    if os.getenv("ENGINE_DEBUG_TIMING"):
        logging.getLogger("engine.timing").setLevel(logging.DEBUG)
    logging.getLogger(__name__).debug("logging configured level=%s", level)


__all__ = ["configure_logging", "KeyValueFormatter"]

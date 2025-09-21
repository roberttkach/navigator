from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from .code import LogCode

REDACT_KEYS = {"path", "inline", "business", "url", "caption", "thumb"}
DEFAULT_MODE = "safe"
_mode = DEFAULT_MODE


def calibrate(mode: str) -> None:
    """Configure log redaction mode."""

    global _mode
    normal = (mode or DEFAULT_MODE).lower()
    if normal not in {"debug", "safe", "paranoid"}:
        normal = DEFAULT_MODE
    _mode = normal


def _targets() -> set[str]:
    base = set(REDACT_KEYS)
    if _mode == "paranoid":
        base.update({"text", "entities"})
    return base


def _filter(v: Any) -> Any:
    if v is None:
        return None
    if isinstance(v, dict):
        keys = _targets()
        return {
            k: ("***" if k in keys and _mode != "debug" else _filter(vv))
            for k, vv in v.items()
        }
    if isinstance(v, (list, tuple)):
        return [_filter(x) for x in v]
    return v


def jlog(logger: logging.Logger, level: int, code: LogCode, **fields: Any) -> None:
    if not logger.isEnabledFor(level):
        return
    scrubbed = _filter(dict(fields))
    trace = bool(scrubbed.pop("exc_info", False))
    payload: Dict[str, Any] = {
        "ts": datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z"),
        "code": code.value,
        **scrubbed,
    }
    logger.log(level, json.dumps(payload, ensure_ascii=False, default=str), exc_info=trace)

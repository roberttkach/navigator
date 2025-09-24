"""Telemetry port implementation backed by :mod:`logging`."""
from __future__ import annotations

import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

from ...core.port.telemetry import LogCode, TelemetryPort


REDACT_KEYS = {"path", "inline", "business", "url", "caption", "thumb"}
DEFAULT_MODE = "safe"


class PythonLoggingTelemetry(TelemetryPort):
    """Emit structured events through the standard logging subsystem."""

    def __init__(self) -> None:
        self._mode = DEFAULT_MODE

    def calibrate(self, mode: str) -> None:
        normal = (mode or DEFAULT_MODE).lower()
        if normal not in {"debug", "safe", "paranoid"}:
            normal = DEFAULT_MODE
        self._mode = normal

    def emit(
        self,
        code: LogCode,
        level: int,
        *,
        origin: str | None = None,
        **fields: Any,
    ) -> None:
        name = origin or "navigator"
        logger = logging.getLogger(name)
        if not logger.isEnabledFor(level):
            return
        scrubbed = self._filter(dict(fields))
        trace = bool(scrubbed.pop("exc_info", False))
        payload: Dict[str, Any] = {
            "ts": datetime.now(timezone.utc)
            .isoformat(timespec="milliseconds")
            .replace("+00:00", "Z"),
            "code": code.value,
            **scrubbed,
        }
        logger.log(level, json.dumps(payload, ensure_ascii=False, default=str), exc_info=trace)

    def _targets(self) -> set[str]:
        base = set(REDACT_KEYS)
        if self._mode == "paranoid":
            base.update({"text", "entities"})
        return base

    def _filter(self, value: Any) -> Any:
        if value is None:
            return None
        if isinstance(value, dict):
            keys = self._targets()
            return {
                key: ("***" if key in keys and self._mode != "debug" else self._filter(inner))
                for key, inner in value.items()
            }
        if isinstance(value, (list, tuple)):
            return [self._filter(item) for item in value]
        return value


__all__ = ["PythonLoggingTelemetry", "LogCode", "TelemetryPort"]

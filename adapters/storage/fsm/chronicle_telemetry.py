"""Telemetry helpers dedicated to chronicle storage events."""
from __future__ import annotations

import logging
from typing import Any

from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel


class ChronicleTelemetry:
    """Emit telemetry events for chronicle operations."""

    def __init__(self, telemetry: Telemetry | None) -> None:
        self._channel: TelemetryChannel | None = (
            telemetry.channel(__name__) if telemetry else None
        )

    def emit(self, level: int, code: LogCode, /, **fields: Any) -> None:
        if self._channel:
            self._channel.emit(level, code, **fields)

    def loaded(self, length: int) -> None:
        self.emit(logging.DEBUG, LogCode.HISTORY_LOAD, history={"len": length})

    def saved(self, length: int) -> None:
        self.emit(logging.DEBUG, LogCode.HISTORY_SAVE, history={"len": length})

    def error(self, note: str, **fields: Any) -> None:
        self.emit(logging.ERROR, LogCode.HISTORY_LOAD, note=note, **fields)


__all__ = ["ChronicleTelemetry"]

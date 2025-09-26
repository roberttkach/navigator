"""Telemetry helpers for edit execution."""

from __future__ import annotations

import logging

from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope


class EditTelemetry:
    """Emit telemetry statements for edit execution."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    def skip(self, note: str) -> None:
        self._channel.emit(logging.INFO, LogCode.RERENDER_START, note=note, skip=True)

    def event(self, note: str) -> None:
        self._channel.emit(logging.INFO, LogCode.RERENDER_START, note=note)

    def inline_blocked(self, scope: Scope, note: str) -> None:
        if scope.inline:
            self._channel.emit(
                logging.INFO,
                LogCode.RERENDER_INLINE_NO_FALLBACK,
                note=note,
                skip=True,
            )


__all__ = ["EditTelemetry"]


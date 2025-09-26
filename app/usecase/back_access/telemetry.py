"""Telemetry helpers decoupled from history writers."""
from __future__ import annotations

import logging

from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel


class RewindWriteTelemetry:
    """Isolate telemetry side-effects for history write operations."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.history.write")

    def state_assigned(self, state: str) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.STATE_SET,
            op="back",
            state={"target": state},
        )

    def latest_marked(self, identifier: int) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.LAST_SET,
            op="back",
            message={"id": identifier},
        )

    def history_saved(self, length: int) -> None:
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op="back",
            history={"len": length},
        )

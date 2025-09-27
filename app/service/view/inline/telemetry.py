"""Telemetry helpers dedicated to inline view reconciliation."""
from __future__ import annotations

import logging

from navigator.core.service.rendering import decision as D
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel


class InlineTelemetryAdapter:
    """Emit inline-related telemetry events."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    def remap_delete_send(self, target: D.Decision) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.INLINE_REMAP_DELETE_SEND,
            origin="DELETE_SEND",
            target=target.name,
        )

    def deny_switch(self) -> None:
        self._channel.emit(logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)


__all__ = ["InlineTelemetryAdapter"]

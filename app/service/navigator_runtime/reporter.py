"""Telemetry reporter used by navigator runtime services."""
from __future__ import annotations

import logging

from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope


class NavigatorReporter:
    """Emit telemetry for navigator operations."""

    def __init__(self, telemetry: Telemetry, scope: Scope) -> None:
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._profile = profile(scope)

    def emit(self, method: str, **fields: object) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method=method,
            scope=self._profile,
            **fields,
        )


__all__ = ["NavigatorReporter"]

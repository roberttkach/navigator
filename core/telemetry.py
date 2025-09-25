"""Expose telemetry helpers for instrumented operations."""
from __future__ import annotations

from dataclasses import dataclass

from typing import Any
from .port.telemetry import LogCode, TelemetryPort


@dataclass(slots=True)
class TelemetryChannel:
    """Immutable helper bound to a particular origin for emitting events."""

    _port: TelemetryPort
    _origin: str

    def emit(self, level: int, code: LogCode, /, **fields: Any) -> None:
        """Forward the telemetry event to the configured port."""

        self._port.emit(code, level, origin=self._origin, **fields)


class Telemetry:
    """Adapter-friendly telemetry hub constructed via dependency injection."""

    def __init__(self, port: TelemetryPort) -> None:
        self._port = port

    def calibrate(self, mode: str) -> None:
        """Adjust the telemetry port configuration for the given mode."""

        self._port.calibrate(mode)

    def channel(self, origin: str) -> TelemetryChannel:
        """Return a channel dedicated to the supplied ``origin`` name."""

        return TelemetryChannel(self._port, origin)


__all__ = ["LogCode", "Telemetry", "TelemetryChannel"]

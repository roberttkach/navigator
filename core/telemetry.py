"""Domain-level façade for telemetry emission."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Optional

from .port.telemetry import LogCode, TelemetryPort


@dataclass(slots=True)
class _TelemetryChannel:
    _hub: "Telemetry"
    _origin: str

    def emit(self, level: int, code: LogCode, /, **fields: Any) -> None:
        """Emit an event via the bound telemetry port."""

        self._hub.emit(code, level, origin=self._origin, **fields)


class Telemetry:
    """Global dispatcher for the telemetry port used across the application."""

    def __init__(self) -> None:
        self._port: Optional[TelemetryPort] = None

    def bind(self, port: TelemetryPort) -> None:
        """Bind a concrete telemetry port implementation."""

        self._port = port

    def bound(self) -> bool:
        """Return whether a telemetry port has been bound."""

        return self._port is not None

    def calibrate(self, mode: str) -> None:
        """Configure the current port redaction/calibration mode."""

        if self._port is not None:
            self._port.calibrate(mode)

    def emit(
        self,
        code: LogCode,
        level: int,
        *,
        origin: str | None = None,
        **fields: Any,
    ) -> None:
        """Emit a structured telemetry event if a port is bound."""

        if self._port is None:
            return
        self._port.emit(code, level, origin=origin, **fields)

    def channel(self, origin: str) -> _TelemetryChannel:
        """Create a lightweight channel bound to a particular origin name."""

        return _TelemetryChannel(self, origin)


telemetry = Telemetry()


__all__ = ["LogCode", "Telemetry", "telemetry"]

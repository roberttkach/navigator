"""Telemetry helpers for the navigator bootstrap sequence."""
from __future__ import annotations

from navigator.adapters.telemetry.logger import PythonLoggingTelemetry
from navigator.core.telemetry import Telemetry


class TelemetryFactory:
    """Build calibrated telemetry instances for the runtime."""

    def create(self) -> Telemetry:
        port = PythonLoggingTelemetry()
        return Telemetry(port)


def calibrate_telemetry(telemetry: Telemetry, redaction: str | None) -> None:
    """Apply telemetry configuration derived from bootstrap settings."""

    telemetry.calibrate(redaction or "")


__all__ = ["TelemetryFactory", "calibrate_telemetry"]

"""Telemetry helpers for the navigator bootstrap sequence."""
from __future__ import annotations

from navigator.adapters.telemetry.logger import PythonLoggingTelemetry
from navigator.core.telemetry import Telemetry


class TelemetryFactory:
    """Build calibrated telemetry instances for the runtime."""

    def create(self) -> Telemetry:
        port = PythonLoggingTelemetry()
        return Telemetry(port)


def calibrate_telemetry(telemetry: Telemetry, container: "AppContainer") -> None:
    """Apply container-level telemetry configuration before runtime assembly."""

    settings = container.core().settings()
    mode = getattr(settings, "redaction", "")
    telemetry.calibrate(mode)


__all__ = ["TelemetryFactory", "calibrate_telemetry"]

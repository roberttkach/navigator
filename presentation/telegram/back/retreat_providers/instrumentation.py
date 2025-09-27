"""Telemetry modules used by retreat provider assembly."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.telemetry import Telemetry

from ..telemetry import RetreatTelemetry


@dataclass(frozen=True)
class RetreatInstrumentationModule:
    """Produce telemetry wrappers for retreat workflows."""

    def build(self, telemetry: Telemetry) -> RetreatTelemetry:
        return RetreatTelemetry(telemetry)


__all__ = ["RetreatInstrumentationModule"]

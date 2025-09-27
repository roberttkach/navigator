"""Shared dataclasses describing runtime plan auxiliary dependencies."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.telemetry import Telemetry

from .reporter import NavigatorReporter
from .tail_components import TailTelemetry
from .types import MissingAlert


@dataclass(frozen=True)
class RuntimeInstrumentationDependencies:
    """Capture telemetry-related collaborators for runtime planning."""

    telemetry: Telemetry | None = None
    tail: TailTelemetry | None = None


@dataclass(frozen=True)
class RuntimeNotificationDependencies:
    """Capture notification components required during runtime planning."""

    reporter: NavigatorReporter | None = None
    missing_alert: MissingAlert | None = None


__all__ = [
    "RuntimeInstrumentationDependencies",
    "RuntimeNotificationDependencies",
]

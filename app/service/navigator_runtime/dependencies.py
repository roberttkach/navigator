"""Definitions for navigator runtime dependency bundles."""

from __future__ import annotations

from dataclasses import dataclass

from navigator.app.locks.guard import Guardian
from navigator.core.telemetry import Telemetry

from .types import MissingAlert
from .usecases import NavigatorUseCases


@dataclass(frozen=True)
class RuntimeDomainServices:
    """Expose domain level collaborators required by the runtime."""

    usecases: NavigatorUseCases


@dataclass(frozen=True)
class RuntimeTelemetryServices:
    """Capture telemetry dependencies for the runtime."""

    telemetry: Telemetry


@dataclass(frozen=True)
class RuntimeSafetyServices:
    """Keep runtime safety and alerting facilities grouped together."""

    guard: Guardian
    missing_alert: MissingAlert | None

    def apply_overrides(
        self,
        *,
        guard: Guardian | None = None,
        missing_alert: MissingAlert | None = None,
    ) -> "RuntimeSafetyServices":
        """Return a new bundle that prefers the provided overrides."""

        return RuntimeSafetyServices(
            guard=guard or self.guard,
            missing_alert=missing_alert or self.missing_alert,
        )


__all__ = [
    "RuntimeDomainServices",
    "RuntimeSafetyServices",
    "RuntimeTelemetryServices",
]

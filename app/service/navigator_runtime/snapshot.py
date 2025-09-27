"""Snapshot representations for navigator runtime exposure."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .dependencies import (
    RuntimeDomainServices,
    RuntimeSafetyServices,
    RuntimeTelemetryServices,
)

if TYPE_CHECKING:
    from navigator.app.locks.guard import Guardian
    from navigator.core.value.message import Scope

    from .activation import RuntimeActivationPlan
    from .types import MissingAlert


@dataclass(frozen=True)
class NavigatorRuntimeSnapshot:
    """Immutable view of runtime dependencies exposed by the container."""

    domain: RuntimeDomainServices
    telemetry: RuntimeTelemetryServices
    safety: RuntimeSafetyServices
    redaction: str

    def create_activation_plan(
        self,
        scope: Scope,
        *,
        guard: Guardian | None = None,
        missing_alert: MissingAlert | None = None,
    ) -> RuntimeActivationPlan:
        """Return an activation plan without exposing internal dependencies."""

        from .activation import RuntimeActivationPlan

        safety = self.safety.apply_overrides(
            guard=guard,
            missing_alert=missing_alert,
        )
        return RuntimeActivationPlan(
            domain=self.domain,
            telemetry=self.telemetry,
            scope=scope,
            safety=safety,
        )


__all__ = ["NavigatorRuntimeSnapshot"]

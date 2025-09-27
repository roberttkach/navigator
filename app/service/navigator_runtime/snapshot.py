"""Snapshot representations for navigator runtime exposure."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from .dependencies import (
    RuntimeDomainServices,
    RuntimeSafetyServices,
    RuntimeTelemetryServices,
)
from .plan import RuntimeActivationPlan

if TYPE_CHECKING:
    from navigator.app.locks.guard import Guardian
    from navigator.core.value.message import Scope

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

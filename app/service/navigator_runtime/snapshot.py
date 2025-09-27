"""Snapshot representations for navigator runtime exposure."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from navigator.app.service.navigator_runtime.dependencies import NavigatorDependencies

if TYPE_CHECKING:
    from navigator.app.locks.guard import Guardian
    from navigator.core.value.message import Scope

    from .activation import RuntimeActivationPlan
    from .types import MissingAlert


@dataclass(frozen=True)
class NavigatorRuntimeSnapshot:
    """Immutable view of runtime dependencies exposed by the container."""

    _dependencies: NavigatorDependencies
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

        dependencies = self._dependencies
        return RuntimeActivationPlan(
            dependencies=dependencies,
            scope=scope,
            guard=guard or dependencies.guard,
            missing_alert=missing_alert or dependencies.missing_alert,
        )


__all__ = ["NavigatorRuntimeSnapshot"]

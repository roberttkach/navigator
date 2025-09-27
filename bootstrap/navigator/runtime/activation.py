"""Runtime activation interfaces decoupling bootstrap from services."""
from __future__ import annotations

from typing import Protocol, TYPE_CHECKING

from navigator.core.contracts import MissingAlert
from navigator.core.value.message import Scope

if TYPE_CHECKING:
    from navigator.app.service.navigator_runtime import NavigatorRuntime
    from navigator.app.service.navigator_runtime.activation import RuntimeActivationPlan
    from navigator.app.service.navigator_runtime.snapshot import NavigatorRuntimeSnapshot


class RuntimeActivationPlanLike(Protocol):
    """Minimal interface required to activate the navigator runtime."""

    def activate(self) -> "NavigatorRuntime":
        ...


class RuntimeActivator(Protocol):
    """Strategy returning activation plans for runtime snapshots."""

    def create_plan(
        self,
        snapshot: "NavigatorRuntimeSnapshot",
        scope: Scope,
        *,
        missing_alert: MissingAlert | None = None,
    ) -> RuntimeActivationPlanLike:
        ...


class NavigatorRuntimeActivationBridge(RuntimeActivator):
    """Bridge service-layer activation helpers into bootstrap interfaces."""

    def create_plan(
        self,
        snapshot: "NavigatorRuntimeSnapshot",
        scope: Scope,
        *,
        missing_alert: MissingAlert | None = None,
    ) -> "RuntimeActivationPlan":
        from navigator.app.service.navigator_runtime.activation import (
            create_activation_plan,
        )

        return create_activation_plan(
            snapshot,
            scope,
            missing_alert=missing_alert,
        )


__all__ = [
    "NavigatorRuntimeActivationBridge",
    "RuntimeActivationPlanLike",
    "RuntimeActivator",
]

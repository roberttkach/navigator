"""Runtime activation interfaces decoupling bootstrap from services."""
from __future__ import annotations

from dataclasses import dataclass, field
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


class RuntimePlanFactory(Protocol):
    """Callable signature creating activation plans for snapshots."""

    def __call__(
        self,
        snapshot: "NavigatorRuntimeSnapshot",
        scope: Scope,
        *,
        missing_alert: MissingAlert | None = None,
    ) -> "RuntimeActivationPlan":
        ...


def _default_plan_factory() -> RuntimePlanFactory:
    from navigator.app.service.navigator_runtime.activation import create_activation_plan

    return create_activation_plan


@dataclass(slots=True)
class NavigatorRuntimeActivationBridge(RuntimeActivator):
    """Bridge service-layer activation helpers into bootstrap interfaces."""

    plan_factory: RuntimePlanFactory = field(default_factory=_default_plan_factory)

    def create_plan(
        self,
        snapshot: "NavigatorRuntimeSnapshot",
        scope: Scope,
        *,
        missing_alert: MissingAlert | None = None,
    ) -> "RuntimeActivationPlan":
        return self.plan_factory(
            snapshot,
            scope,
            missing_alert=missing_alert,
        )


__all__ = [
    "NavigatorRuntimeActivationBridge",
    "RuntimeActivationPlanLike",
    "RuntimeActivator",
]

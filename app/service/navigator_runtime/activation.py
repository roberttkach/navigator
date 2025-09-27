"""Activation plans translating snapshots into runnable runtimes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope

from .runtime_factory import build_navigator_runtime
from .dependencies import NavigatorDependencies
from .runtime import NavigatorRuntime
from .types import MissingAlert

if TYPE_CHECKING:
    from .snapshot import NavigatorRuntimeSnapshot


@dataclass(frozen=True)
class RuntimeActivationPlan:
    """Immutable description of how to activate the navigator runtime."""

    dependencies: NavigatorDependencies
    scope: Scope
    guard: Guardian
    missing_alert: MissingAlert | None

    def activate(self) -> NavigatorRuntime:
        """Build a runtime instance according to the stored plan."""

        return build_navigator_runtime(
            usecases=self.dependencies.usecases,
            scope=self.scope,
            guard=self.guard,
            telemetry=self.dependencies.telemetry,
            missing_alert=self.missing_alert,
        )


def create_activation_plan(
    snapshot: NavigatorRuntimeSnapshot,
    scope: Scope,
    *,
    guard: Guardian | None = None,
    missing_alert: MissingAlert | None = None,
) -> RuntimeActivationPlan:
    """Derive a runtime activation plan from container snapshot data."""

    return snapshot.create_activation_plan(
        scope,
        guard=guard,
        missing_alert=missing_alert,
    )


__all__ = ["RuntimeActivationPlan", "create_activation_plan"]

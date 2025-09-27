"""High level helpers to build navigator runtime instances."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope

from .activation import RuntimeActivationPlan
from .dependencies import NavigatorDependencies
from .runtime import NavigatorRuntime
from .types import MissingAlert


def build_runtime_from_dependencies(
    dependencies: NavigatorDependencies,
    scope: Scope,
    *,
    guard: Guardian | None = None,
    missing_alert: MissingAlert | None = None,
) -> NavigatorRuntime:
    """Compose a :class:`NavigatorRuntime` from resolved dependencies."""

    plan = RuntimeActivationPlan(
        dependencies=dependencies,
        scope=scope,
        guard=guard or dependencies.guard,
        missing_alert=missing_alert or dependencies.missing_alert,
    )
    return plan.activate()


__all__ = ["build_runtime_from_dependencies"]

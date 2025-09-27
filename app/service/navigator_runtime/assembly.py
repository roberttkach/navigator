"""High level helpers to build navigator runtime instances."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope

from .runtime import NavigatorRuntime
from .snapshot import NavigatorRuntimeSnapshot
from .types import MissingAlert


def build_runtime_from_dependencies(
    snapshot: NavigatorRuntimeSnapshot,
    scope: Scope,
    *,
    guard: Guardian | None = None,
    missing_alert: MissingAlert | None = None,
) -> NavigatorRuntime:
    """Compose a :class:`NavigatorRuntime` from resolved dependencies."""

    plan = snapshot.create_activation_plan(
        scope,
        guard=guard,
        missing_alert=missing_alert,
    )
    return plan.activate()


__all__ = ["build_runtime_from_dependencies"]

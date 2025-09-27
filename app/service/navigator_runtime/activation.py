"""Activation plans translating snapshots into runnable runtimes."""
from __future__ import annotations

from typing import TYPE_CHECKING

from navigator.core.value.message import Scope

from .plan import RuntimeActivationPlan

if TYPE_CHECKING:
    from navigator.app.locks.guard import Guardian

    from .snapshot import NavigatorRuntimeSnapshot
    from .types import MissingAlert


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

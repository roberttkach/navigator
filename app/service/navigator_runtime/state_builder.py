"""Helpers for composing navigator state services."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope

from .contracts import StateContracts
from .reporter import NavigatorReporter
from .state import MissingStateAlarm, NavigatorStateService
from .types import MissingAlert


def build_state_service(
    contracts: StateContracts,
    *,
    guard: Guardian,
    scope: Scope,
    reporter: NavigatorReporter,
    missing_alert: MissingAlert | None,
) -> NavigatorStateService:
    """Create navigator state services with explicit dependencies."""

    alarm = MissingStateAlarm(
        alarm=contracts.alarm,
        scope=scope,
        factory=missing_alert,
    )
    return NavigatorStateService(
        setter=contracts.setter,
        alarm=contracts.alarm,
        guard=guard,
        scope=scope,
        reporter=reporter,
        missing_alarm=alarm,
    )


__all__ = ["build_state_service"]

"""Helpers for composing navigator state services."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope

from .contracts import StateContracts
from .reporter import NavigatorReporter
from .state import (
    MissingStateAlarm,
    NavigatorStateService,
    StateAlertManager,
    StateOperationExecutor,
)
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

    missing = (
        MissingStateAlarm(
            alarm=contracts.alarm,
            scope=scope,
            factory=missing_alert,
        )
        if missing_alert
        else None
    )
    alerts = StateAlertManager(
        alarm=contracts.alarm,
        scope=scope,
        missing_alarm=missing,
    )
    operations = StateOperationExecutor(
        setter=contracts.setter,
        guard=guard,
        scope=scope,
        alerts=alerts,
    )
    return NavigatorStateService(
        operations=operations,
        reporter=reporter,
    )


__all__ = ["build_state_service"]

"""Navigator assembly helpers decoupled from dependency container details."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.locks.guard import Guardian
from navigator.app.service.navigator_runtime import MissingAlert, NavigatorUseCases
from navigator.app.service import build_navigator_runtime
from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope
from navigator.presentation.navigator import Navigator


@dataclass(frozen=True)
class NavigatorDependencies:
    """Minimal set of services required to assemble a navigator runtime."""

    usecases: NavigatorUseCases
    guard: Guardian
    telemetry: Telemetry
    missing_alert: MissingAlert


def compose(
    dependencies: NavigatorDependencies,
    scope: Scope,
    *,
    guard: Guardian | None = None,
    missing_alert: MissingAlert | None = None,
) -> Navigator:
    """Construct a Navigator facade from resolved runtime dependencies."""

    runtime = build_navigator_runtime(
        usecases=dependencies.usecases,
        scope=scope,
        guard=guard or dependencies.guard,
        telemetry=dependencies.telemetry,
        missing_alert=missing_alert or dependencies.missing_alert,
    )
    return Navigator(runtime)


__all__ = ["NavigatorDependencies", "compose"]

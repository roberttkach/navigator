"""Navigator assembly helpers decoupled from dependency container details."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.app.service import build_navigator_runtime
from navigator.app.service.navigator_runtime import MissingAlert, NavigatorRuntime
from navigator.app.service.navigator_runtime.dependencies import NavigatorDependencies
from navigator.core.value.message import Scope
from navigator.presentation.navigator import Navigator


def build_runtime(
    dependencies: NavigatorDependencies,
    scope: Scope,
    *,
    guard: Guardian | None = None,
    missing_alert: MissingAlert | None = None,
) -> NavigatorRuntime:
    """Construct a navigator runtime from resolved dependencies."""

    return build_navigator_runtime(
        usecases=dependencies.usecases,
        scope=scope,
        guard=guard or dependencies.guard,
        telemetry=dependencies.telemetry,
        missing_alert=missing_alert or dependencies.missing_alert,
    )


def wrap_runtime(runtime: NavigatorRuntime) -> Navigator:
    """Wrap the navigator runtime with presentation facade."""

    return Navigator(runtime)


def compose(
    dependencies: NavigatorDependencies,
    scope: Scope,
    *,
    guard: Guardian | None = None,
    missing_alert: MissingAlert | None = None,
) -> Navigator:
    """Construct a Navigator facade from resolved runtime dependencies."""

    runtime = build_runtime(
        dependencies,
        scope,
        guard=guard,
        missing_alert=missing_alert,
    )
    return wrap_runtime(runtime)


__all__ = ["NavigatorDependencies", "build_runtime", "compose", "wrap_runtime"]

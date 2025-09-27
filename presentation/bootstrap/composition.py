"""High level helpers building navigators from runtime dependencies."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.core.contracts import MissingAlert
from navigator.core.value.message import Scope
from navigator.presentation.navigator import Navigator

from .composer import NavigatorComposer, NavigatorRuntime, NavigatorRuntimeSnapshot
from .runtime_gateway import NavigatorRuntimePort, default_runtime_port


def build_runtime(
    dependencies: NavigatorRuntimeSnapshot,
    scope: Scope,
    *,
    guard: Guardian | None = None,
    missing_alert: MissingAlert | None = None,
    runtime_port: NavigatorRuntimePort | None = None,
) -> NavigatorRuntime:
    """Construct a navigator runtime from resolved dependencies."""

    port = runtime_port or default_runtime_port()
    composer = NavigatorComposer(port)
    return composer.build_runtime(
        dependencies,
        scope,
        guard=guard,
        missing_alert=missing_alert,
    )


def wrap_runtime(runtime: NavigatorRuntime) -> Navigator:
    """Wrap the navigator runtime with presentation facade."""

    return Navigator(runtime)


def compose(
    dependencies: NavigatorRuntimeSnapshot,
    scope: Scope,
    *,
    guard: Guardian | None = None,
    missing_alert: MissingAlert | None = None,
    runtime_port: NavigatorRuntimePort | None = None,
) -> Navigator:
    """Construct a Navigator facade from resolved runtime dependencies."""

    port = runtime_port or default_runtime_port()
    composer = NavigatorComposer(port)
    return composer.compose(
        dependencies,
        scope,
        guard=guard,
        missing_alert=missing_alert,
    )


__all__ = ["build_runtime", "compose", "wrap_runtime"]

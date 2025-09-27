"""Bootstrap helpers assembling presentation navigators."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from navigator.app.locks.guard import Guardian
from navigator.core.contracts import MissingAlert
from navigator.core.value.message import Scope
from navigator.presentation.navigator import Navigator

from .runtime_gateway import (
    NavigatorRuntimePort,
    RuntimeRequest,
    default_runtime_port,
)

if TYPE_CHECKING:
    from navigator.app.service.navigator_runtime.dependencies import NavigatorDependencies
    from navigator.app.service.navigator_runtime.runtime import NavigatorRuntime
else:  # pragma: no cover - runtime typing fallback
    NavigatorDependencies = Any
    NavigatorRuntime = Any


@dataclass(frozen=True)
class NavigatorComposer:
    """Compose navigators using an injected runtime factory."""

    runtime_port: NavigatorRuntimePort

    def build_runtime(
        self,
        dependencies: NavigatorDependencies,
        scope: Scope,
        *,
        guard: Guardian | None = None,
        missing_alert: MissingAlert | None = None,
    ) -> NavigatorRuntime:
        request = RuntimeRequest(scope=scope, guard=guard, missing_alert=missing_alert)
        return self.runtime_port.create_runtime(dependencies, request)

    def compose(
        self,
        dependencies: NavigatorDependencies,
        scope: Scope,
        *,
        guard: Guardian | None = None,
        missing_alert: MissingAlert | None = None,
    ) -> Navigator:
        runtime = self.build_runtime(
            dependencies,
            scope,
            guard=guard,
            missing_alert=missing_alert,
        )
        return wrap_runtime(runtime)


def build_runtime(
    dependencies: NavigatorDependencies,
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
    dependencies: NavigatorDependencies,
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


__all__ = [
    "NavigatorComposer",
    "build_runtime",
    "compose",
    "wrap_runtime",
]

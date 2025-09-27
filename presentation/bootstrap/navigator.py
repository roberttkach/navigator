"""Navigator assembly helpers decoupled from dependency container details."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.locks.guard import Guardian
from navigator.app.service.navigator_runtime.dependencies import NavigatorDependencies
from navigator.app.service.navigator_runtime.runtime import NavigatorRuntime
from navigator.core.contracts import MissingAlert
from navigator.core.value.message import Scope
from navigator.presentation.navigator import Navigator

from .runtime_factory import NavigatorRuntimeFactory, default_runtime_factory


@dataclass(frozen=True)
class NavigatorComposer:
    """Compose navigators using an injected runtime factory."""

    runtime_factory: NavigatorRuntimeFactory

    def build_runtime(
        self,
        dependencies: NavigatorDependencies,
        scope: Scope,
        *,
        guard: Guardian | None = None,
        missing_alert: MissingAlert | None = None,
    ) -> NavigatorRuntime:
        return self.runtime_factory(
            dependencies,
            scope,
            guard=guard,
            missing_alert=missing_alert,
        )

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
    runtime_factory: NavigatorRuntimeFactory | None = None,
) -> NavigatorRuntime:
    """Construct a navigator runtime from resolved dependencies."""

    factory = runtime_factory or default_runtime_factory()
    composer = NavigatorComposer(factory)
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
    runtime_factory: NavigatorRuntimeFactory | None = None,
) -> Navigator:
    """Construct a Navigator facade from resolved runtime dependencies."""

    factory = runtime_factory or default_runtime_factory()
    composer = NavigatorComposer(factory)
    return composer.compose(
        dependencies,
        scope,
        guard=guard,
        missing_alert=missing_alert,
    )


__all__ = [
    "NavigatorComposer",
    "NavigatorDependencies",
    "build_runtime",
    "compose",
    "wrap_runtime",
]

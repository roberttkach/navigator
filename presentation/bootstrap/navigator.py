"""Navigator assembly helpers."""
from __future__ import annotations

from typing import Protocol

from navigator.app.locks.guard import Guardian
from navigator.app.service import build_navigator_runtime
from navigator.app.service.navigator_runtime import NavigatorUseCases
from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope
from navigator.presentation.alerts import missing
from navigator.presentation.navigator import Navigator


class _Core(Protocol):
    def guard(self) -> Guardian: ...

    def telemetry(self) -> Telemetry: ...


class _UsecaseBundle(Protocol):
    def navigator(self) -> NavigatorUseCases: ...


class NavigatorContainer(Protocol):
    def core(self) -> _Core: ...

    def usecases(self) -> _UsecaseBundle: ...


def compose(
    container: NavigatorContainer,
    scope: Scope,
    *,
    guard: Guardian | None = None,
) -> Navigator:
    """Construct a Navigator facade from a DI container."""

    core = container.core()
    bundle = container.usecases().navigator()
    sentinel = guard or core.guard()
    runtime = build_navigator_runtime(
        usecases=bundle,
        scope=scope,
        guard=sentinel,
        telemetry=core.telemetry(),
        missing_alert=missing,
    )
    return Navigator(runtime)


__all__ = ["compose", "NavigatorContainer"]

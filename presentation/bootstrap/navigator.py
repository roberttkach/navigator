"""Navigator assembly helpers."""
from __future__ import annotations

from typing import Protocol

from navigator.app.locks.guard import Guardian
from navigator.app.service import build_navigator_runtime
from navigator.app.usecase.add import Appender
from navigator.app.usecase.alarm import Alarm
from navigator.app.usecase.back import Rewinder
from navigator.app.usecase.last import Tailer
from navigator.app.usecase.pop import Trimmer
from navigator.app.usecase.rebase import Shifter
from navigator.app.usecase.replace import Swapper
from navigator.app.usecase.set import Setter
from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope
from navigator.presentation.navigator import Navigator


class _Core(Protocol):
    def guard(self) -> Guardian: ...

    def telemetry(self) -> Telemetry: ...


class _Usecases(Protocol):
    def appender(self) -> Appender: ...

    def swapper(self) -> Swapper: ...

    def rewinder(self) -> Rewinder: ...

    def setter(self) -> Setter: ...

    def trimmer(self) -> Trimmer: ...

    def shifter(self) -> Shifter: ...

    def tailer(self) -> Tailer: ...

    def alarm(self) -> Alarm: ...


class NavigatorContainer(Protocol):
    def core(self) -> _Core: ...

    def usecases(self) -> _Usecases: ...


def compose(
    container: NavigatorContainer,
    scope: Scope,
    *,
    guard: Guardian | None = None,
) -> Navigator:
    """Construct a Navigator facade from a DI container."""

    core = container.core()
    usecases = container.usecases()
    sentinel = guard or core.guard()
    runtime = build_navigator_runtime(
        appender=usecases.appender(),
        swapper=usecases.swapper(),
        rewinder=usecases.rewinder(),
        setter=usecases.setter(),
        trimmer=usecases.trimmer(),
        shifter=usecases.shifter(),
        tailer=usecases.tailer(),
        alarm=usecases.alarm(),
        scope=scope,
        guard=sentinel,
        telemetry=core.telemetry(),
    )
    return Navigator(runtime)


__all__ = ["compose", "NavigatorContainer"]

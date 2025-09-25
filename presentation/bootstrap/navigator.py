"""Navigator assembly helpers."""
from __future__ import annotations

from typing import Protocol

from ...app.locks.guard import GuardFactory
from ...app.usecase.add import Appender
from ...app.usecase.alarm import Alarm
from ...app.usecase.back import Rewinder
from ...app.usecase.last import Tailer
from ...app.usecase.pop import Trimmer
from ...app.usecase.rebase import Shifter
from ...app.usecase.replace import Swapper
from ...app.usecase.set import Setter
from ...core.telemetry import Telemetry
from ...core.value.message import Scope
from ..navigator import Navigator


class _Core(Protocol):
    def guard(self) -> GuardFactory: ...
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
    guard: GuardFactory | None = None,
) -> Navigator:
    """Construct a Navigator facade from a DI container."""

    core = container.core()
    usecases = container.usecases()
    sentinel = guard or core.guard()
    return Navigator(
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


__all__ = ["compose", "NavigatorContainer"]

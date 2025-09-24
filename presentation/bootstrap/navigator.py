"""Navigator assembly helpers."""
from __future__ import annotations

from typing import Protocol

from ...application.locks.guard import GuardFactory
from ...application.usecase.add import Appender
from ...application.usecase.alarm import Alarm
from ...application.usecase.back import Rewinder
from ...application.usecase.last import Tailer
from ...application.usecase.pop import Trimmer
from ...application.usecase.rebase import Shifter
from ...application.usecase.replace import Swapper
from ...application.usecase.set import Setter
from ...domain.value.message import Scope
from ..navigator import Navigator


class _Core(Protocol):
    def guard(self) -> GuardFactory: ...


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


def build_navigator(
    container: NavigatorContainer,
    scope: Scope,
    *,
    guard: GuardFactory | None = None,
) -> Navigator:
    """Construct a Navigator facade from a DI container."""

    core = container.core()
    usecases = container.usecases()
    guard_factory = guard or core.guard()
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
        guard=guard_factory,
    )


__all__ = ["build_navigator", "NavigatorContainer"]

"""State-related helpers used by the navigator runtime."""
from __future__ import annotations

from typing import Any, Protocol

from navigator.app.locks.guard import Guardian
from navigator.app.usecase.alarm import Alarm
from navigator.app.usecase.set import Setter
from navigator.core.error import StateNotFound
from navigator.core.value.message import Scope

from .reporter import NavigatorReporter
from .types import MissingAlert


class StateDescriptor(Protocol):
    """Minimal protocol describing state holders used by the runtime."""

    state: str


class MissingStateAlarm:
    """Coordinate missing-state notifications via the alarm use case."""

    def __init__(
        self,
        *,
        alarm: Alarm,
        scope: Scope,
        factory: MissingAlert | None = None,
    ) -> None:
        self._alarm = alarm
        self._scope = scope
        self._factory = factory

    async def trigger(self) -> None:
        payload = self._factory(self._scope) if self._factory else None
        await self._alarm.execute(self._scope, text=payload)


class NavigatorStateService:
    """Coordinate state assignments and alerts."""

    def __init__(
        self,
        *,
        setter: Setter,
        alarm: Alarm,
        guard: Guardian,
        scope: Scope,
        reporter: NavigatorReporter,
        missing_alarm: MissingStateAlarm | None = None,
    ) -> None:
        self._setter = setter
        self._alarm = alarm
        self._guard = guard
        self._scope = scope
        self._reporter = reporter
        self._missing_alarm = missing_alarm

    async def set(
        self,
        state: str | StateDescriptor,
        context: dict[str, Any] | None = None,
    ) -> None:
        status = getattr(state, "state", state)
        self._reporter.emit("set", state=status)
        async with self._guard(self._scope):
            try:
                await self._setter.execute(self._scope, status, context or {})
            except StateNotFound:
                if self._missing_alarm:
                    await self._missing_alarm.trigger()
                else:
                    await self._alarm.execute(self._scope)

    async def alert(self) -> None:
        self._reporter.emit("alert")
        async with self._guard(self._scope):
            await self._alarm.execute(self._scope)


__all__ = ["NavigatorStateService", "MissingStateAlarm", "StateDescriptor"]

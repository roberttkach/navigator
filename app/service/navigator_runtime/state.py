"""State-related helpers used by the navigator runtime."""
from __future__ import annotations

from typing import Any, Protocol

from navigator.app.locks.guard import Guardian
from navigator.core.error import StateNotFound
from navigator.core.value.message import Scope

from .reporter import NavigatorReporter
from .ports import AlarmUseCase, SetStateUseCase
from .types import MissingAlert


class StateDescriptor(Protocol):
    """Minimal protocol describing state holders used by the runtime."""

    state: str


class MissingStateAlarm:
    """Coordinate missing-state notifications via the alarm use case."""

    def __init__(
        self,
        *,
        alarm: AlarmUseCase,
        scope: Scope,
        factory: MissingAlert | None = None,
    ) -> None:
        self._alarm = alarm
        self._scope = scope
        self._factory = factory

    async def trigger(self) -> None:
        payload = self._factory(self._scope) if self._factory else None
        await self._alarm.execute(self._scope, text=payload)


class StateAlertManager:
    """Bundle alert handling policies independent from service orchestration."""

    def __init__(
        self,
        *,
        alarm: AlarmUseCase,
        scope: Scope,
        missing_alarm: MissingStateAlarm | None = None,
    ) -> None:
        self._alarm = alarm
        self._scope = scope
        self._missing_alarm = missing_alarm

    async def missing(self) -> None:
        if self._missing_alarm:
            await self._missing_alarm.trigger()
        else:
            await self._alarm.execute(self._scope)

    async def notify(self) -> None:
        await self._alarm.execute(self._scope)


class StateOperationExecutor:
    """Execute state transitions under guard while delegating alerts."""

    def __init__(
        self,
        *,
        setter: SetStateUseCase,
        guard: Guardian,
        scope: Scope,
        alerts: StateAlertManager,
    ) -> None:
        self._setter = setter
        self._guard = guard
        self._scope = scope
        self._alerts = alerts

    async def assign(self, status: str, context: dict[str, Any]) -> None:
        async with self._guard(self._scope):
            try:
                await self._setter.execute(self._scope, status, context)
            except StateNotFound:
                await self._alerts.missing()

    async def alert(self) -> None:
        async with self._guard(self._scope):
            await self._alerts.notify()


class NavigatorStateService:
    """Coordinate state assignments and alerts."""

    def __init__(
        self,
        *,
        operations: StateOperationExecutor,
        reporter: NavigatorReporter,
    ) -> None:
        self._operations = operations
        self._reporter = reporter

    async def set(
        self,
        state: str | StateDescriptor,
        context: dict[str, Any] | None = None,
    ) -> None:
        status = getattr(state, "state", state)
        self._reporter.emit("set", state=status)
        await self._operations.assign(status, context or {})

    async def alert(self) -> None:
        self._reporter.emit("alert")
        await self._operations.alert()


__all__ = [
    "MissingStateAlarm",
    "NavigatorStateService",
    "StateAlertManager",
    "StateDescriptor",
    "StateOperationExecutor",
]

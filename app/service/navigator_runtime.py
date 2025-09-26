"""Navigator runtime orchestration helpers.

These helpers live in the application layer to keep the presentation
facade thin. They coordinate payload bundling, telemetry emission and
locking around the low level use cases that mutate navigator state.
"""
from __future__ import annotations

import logging
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Any, Awaitable, Callable, Protocol, SupportsInt

from navigator.app.dto.content import Content, Node
from navigator.app.locks.guard import Guardian
from navigator.app.map.payload import collect, convert
from navigator.app.usecase.add import Appender
from navigator.app.usecase.alarm import Alarm
from navigator.app.usecase.back import Rewinder
from navigator.app.usecase.last import Tailer
from navigator.app.usecase.pop import Trimmer
from navigator.app.usecase.rebase import Shifter
from navigator.app.usecase.replace import Swapper
from navigator.app.usecase.set import Setter
from navigator.core.error import StateNotFound
from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope


class _StateDescriptor(Protocol):
    """Minimal protocol describing state holders used by the runtime."""

    state: str


MissingAlert = Callable[[Scope], str]


class PayloadBundler:
    """Transform DTO content into payload bundles."""

    def bundle(self, content: Content | Node) -> list[Payload]:
        node = content if isinstance(content, Node) else Node(messages=[content])
        return collect(node)


class _HistoryOperation:
    """Base helper coordinating guard and telemetry for history actions."""

    def __init__(
        self,
        *,
        guard: Guardian,
        scope: Scope,
        reporter: NavigatorReporter,
    ) -> None:
        self._guard = guard
        self._scope = scope
        self._reporter = reporter

    async def _run(
        self,
        method: str,
        action: Callable[[], Awaitable[None]],
        **fields: object,
    ) -> None:
        self._reporter.emit(method, **fields)
        async with self._guard(self._scope):
            await action()


class HistoryAddOperation(_HistoryOperation):
    """Append payloads to history while guarding shared resources."""

    def __init__(
        self,
        *,
        appender: Appender,
        bundler: PayloadBundler,
        guard: Guardian,
        scope: Scope,
        reporter: NavigatorReporter,
    ) -> None:
        super().__init__(guard=guard, scope=scope, reporter=reporter)
        self._appender = appender
        self._bundler = bundler

    async def __call__(
        self,
        content: Content | Node,
        *,
        key: str | None = None,
        root: bool = False,
    ) -> None:
        payloads = self._bundler.bundle(content)

        async def action() -> None:
            await self._appender.execute(self._scope, payloads, key, root=root)

        await self._run(
            "add",
            action,
            key=key,
            root=root,
            payload={"count": len(payloads)},
        )


class HistoryReplaceOperation(_HistoryOperation):
    """Replace tail payloads with new content."""

    def __init__(
        self,
        *,
        swapper: Swapper,
        bundler: PayloadBundler,
        guard: Guardian,
        scope: Scope,
        reporter: NavigatorReporter,
    ) -> None:
        super().__init__(guard=guard, scope=scope, reporter=reporter)
        self._swapper = swapper
        self._bundler = bundler

    async def __call__(self, content: Content | Node) -> None:
        payloads = self._bundler.bundle(content)

        async def action() -> None:
            await self._swapper.execute(self._scope, payloads)

        await self._run("replace", action, payload={"count": len(payloads)})


class HistoryRebaseOperation(_HistoryOperation):
    """Rebase history markers around a specific message identifier."""

    def __init__(
        self,
        *,
        shifter: Shifter,
        guard: Guardian,
        scope: Scope,
        reporter: NavigatorReporter,
    ) -> None:
        super().__init__(guard=guard, scope=scope, reporter=reporter)
        self._shifter = shifter

    async def __call__(self, message: int | SupportsInt) -> None:
        identifier = getattr(message, "id", message)

        async def action() -> None:
            await self._shifter.execute(int(identifier))

        await self._run("rebase", action, message={"id": int(identifier)})


class HistoryBackOperation(_HistoryOperation):
    """Drive backtracking with guard and telemetry instrumentation."""

    def __init__(
        self,
        *,
        rewinder: Rewinder,
        guard: Guardian,
        scope: Scope,
        reporter: NavigatorReporter,
    ) -> None:
        super().__init__(guard=guard, scope=scope, reporter=reporter)
        self._rewinder = rewinder

    async def __call__(self, context: dict[str, Any]) -> None:
        handlers = sorted(context.keys()) if isinstance(context, Mapping) else None

        async def action() -> None:
            await self._rewinder.execute(self._scope, context)

        await self._run("back", action, handlers=handlers)


class HistoryTrimOperation(_HistoryOperation):
    """Trim history entries with guard orchestration."""

    def __init__(
        self,
        *,
        trimmer: Trimmer,
        guard: Guardian,
        scope: Scope,
        reporter: NavigatorReporter,
    ) -> None:
        super().__init__(guard=guard, scope=scope, reporter=reporter)
        self._trimmer = trimmer

    async def __call__(self, count: int = 1) -> None:

        async def action() -> None:
            await self._trimmer.execute(count)

        await self._run("pop", action, count=count)


class NavigatorReporter:
    """Emit telemetry for navigator operations."""

    def __init__(self, telemetry: Telemetry, scope: Scope) -> None:
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._profile = profile(scope)

    def emit(self, method: str, **fields: object) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method=method,
            scope=self._profile,
            **fields,
        )


class NavigatorTail:
    """Expose tail operations guarded by telemetry and locking."""

    def __init__(
        self,
        *,
        flow: Tailer,
        scope: Scope,
        guard: Guardian,
        telemetry: Telemetry,
    ) -> None:
        self._tailer = flow
        self._scope = scope
        self._guard = guard
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._profile = profile(scope)

    async def get(self) -> dict[str, object] | None:
        self._emit("last.get")
        async with self._guard(self._scope):
            identifier = await self._tailer.peek()
        if identifier is None:
            return None
        return {
            "id": identifier,
            "inline": bool(self._scope.inline),
            "chat": self._scope.chat,
        }

    async def delete(self) -> None:
        self._emit("last.delete")
        async with self._guard(self._scope):
            await self._tailer.delete(self._scope)

    async def edit(self, content: Content) -> int | None:
        self._emit(
            "last.edit",
            payload={
                "text": bool(content.text),
                "media": bool(content.media),
                "group": bool(content.group),
            },
        )
        async with self._guard(self._scope):
            result = await self._tailer.edit(self._scope, convert(content))
        return result

    def _emit(self, method: str, **fields: object) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method=method,
            scope=self._profile,
            **fields,
        )


class NavigatorHistoryService:
    """Coordinate history-centric operations via dedicated actions."""

    def __init__(
        self,
        *,
        add: HistoryAddOperation,
        replace: HistoryReplaceOperation,
        rebase: HistoryRebaseOperation,
        back: HistoryBackOperation,
        pop: HistoryTrimOperation,
    ) -> None:
        self._add = add
        self._replace = replace
        self._rebase = rebase
        self._back = back
        self._pop = pop

    async def add(
        self,
        content: Content | Node,
        *,
        key: str | None = None,
        root: bool = False,
    ) -> None:
        await self._add(content, key=key, root=root)

    async def replace(self, content: Content | Node) -> None:
        await self._replace(content)

    async def rebase(self, message: int | SupportsInt) -> None:
        await self._rebase(message)

    async def back(self, context: dict[str, Any]) -> None:
        await self._back(context)

    async def pop(self, count: int = 1) -> None:
        await self._pop(count)


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
        state: str | _StateDescriptor,
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


@dataclass(frozen=True)
class NavigatorUseCases:
    """Bundle of use cases required to assemble the navigator runtime."""

    appender: Appender
    swapper: Swapper
    rewinder: Rewinder
    setter: Setter
    trimmer: Trimmer
    shifter: Shifter
    tailer: Tailer
    alarm: Alarm


@dataclass(frozen=True)
class NavigatorRuntime:
    """Collection of navigator application services."""

    history: NavigatorHistoryService
    state: NavigatorStateService
    tail: NavigatorTail


def build_navigator_runtime(
    *,
    usecases: NavigatorUseCases,
    scope: Scope,
    guard: Guardian,
    telemetry: Telemetry,
    bundler: PayloadBundler | None = None,
    reporter: NavigatorReporter | None = None,
    missing_alert: MissingAlert | None = None,
) -> NavigatorRuntime:
    """Create a navigator runtime wiring use cases with cross-cutting tools."""

    bundler = bundler or PayloadBundler()
    reporter = reporter or NavigatorReporter(telemetry, scope)
    add_operation = HistoryAddOperation(
        appender=usecases.appender,
        bundler=bundler,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    replace_operation = HistoryReplaceOperation(
        swapper=usecases.swapper,
        bundler=bundler,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    rebase_operation = HistoryRebaseOperation(
        shifter=usecases.shifter,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    back_operation = HistoryBackOperation(
        rewinder=usecases.rewinder,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    trim_operation = HistoryTrimOperation(
        trimmer=usecases.trimmer,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    history = NavigatorHistoryService(
        add=add_operation,
        replace=replace_operation,
        rebase=rebase_operation,
        back=back_operation,
        pop=trim_operation,
    )
    missing_state_alarm = MissingStateAlarm(
        alarm=usecases.alarm,
        scope=scope,
        factory=missing_alert,
    )
    state = NavigatorStateService(
        setter=usecases.setter,
        alarm=usecases.alarm,
        guard=guard,
        scope=scope,
        reporter=reporter,
        missing_alarm=missing_state_alarm,
    )
    tail = NavigatorTail(
        flow=usecases.tailer,
        scope=scope,
        guard=guard,
        telemetry=telemetry,
    )
    return NavigatorRuntime(history=history, state=state, tail=tail)


__all__ = [
    "NavigatorUseCases",
    "NavigatorRuntime",
    "NavigatorHistoryService",
    "NavigatorStateService",
    "MissingStateAlarm",
    "NavigatorTail",
    "NavigatorReporter",
    "PayloadBundler",
    "build_navigator_runtime",
]

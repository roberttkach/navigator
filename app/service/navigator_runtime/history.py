"""History-oriented operations orchestrated by the navigator runtime."""
from __future__ import annotations

from collections.abc import Mapping
from typing import Any, Awaitable, Callable, SupportsInt

from navigator.app.dto.content import Content, Node
from navigator.app.locks.guard import Guardian
from navigator.app.usecase.add import Appender
from navigator.app.usecase.back import Rewinder
from navigator.app.usecase.pop import Trimmer
from navigator.app.usecase.rebase import Shifter
from navigator.app.usecase.replace import Swapper
from navigator.app.usecase.set import Setter

from .bundler import PayloadBundler
from .reporter import NavigatorReporter


class _HistoryOperation:
    """Base helper coordinating guard and telemetry for history actions."""

    def __init__(
        self,
        *,
        guard: Guardian,
        scope,
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
        scope,
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
        scope,
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
        scope,
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
        scope,
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
        scope,
        reporter: NavigatorReporter,
    ) -> None:
        super().__init__(guard=guard, scope=scope, reporter=reporter)
        self._trimmer = trimmer

    async def __call__(self, count: int = 1) -> None:

        async def action() -> None:
            await self._trimmer.execute(count)

        await self._run("pop", action, count=count)


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


__all__ = [
    "HistoryAddOperation",
    "HistoryBackOperation",
    "HistoryRebaseOperation",
    "HistoryReplaceOperation",
    "HistoryTrimOperation",
    "NavigatorHistoryService",
]

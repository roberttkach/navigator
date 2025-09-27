"""History operation implementations coordinated by the runtime."""
from __future__ import annotations

from typing import SupportsInt

from navigator.app.locks.guard import Guardian
from navigator.core.contracts.back import NavigatorBackContext

from ..bundler import PayloadBundleSource, PayloadBundler
from ..ports import (
    RebaseHistoryUseCase,
    ReplaceHistoryUseCase,
    RewindHistoryUseCase,
    TrimHistoryUseCase,
)
from ..reporter import NavigatorReporter
from .appender import HistoryPayloadAppender
from .base import _HistoryOperation


class HistoryAddOperation(_HistoryOperation):
    """Append payloads to history while guarding shared resources."""

    def __init__(
        self,
        *,
        payloads: HistoryPayloadAppender,
        guard: Guardian,
        scope,
        reporter: NavigatorReporter,
    ) -> None:
        super().__init__(guard=guard, scope=scope, reporter=reporter)
        self._payloads = payloads

    async def __call__(
        self,
        content: PayloadBundleSource,
        *,
        key: str | None = None,
        root: bool = False,
    ) -> None:
        request = self._payloads.prepare(content, key=key, root=root)

        async def action() -> None:
            await self._payloads.append(self._scope, request)

        await self._run(
            "add",
            action,
            key=request.key,
            root=request.root,
            payload={"count": request.count},
        )


class HistoryReplaceOperation(_HistoryOperation):
    """Replace tail payloads with new content."""

    def __init__(
        self,
        *,
        swapper: ReplaceHistoryUseCase,
        bundler: PayloadBundler,
        guard: Guardian,
        scope,
        reporter: NavigatorReporter,
    ) -> None:
        super().__init__(guard=guard, scope=scope, reporter=reporter)
        self._swapper = swapper
        self._bundler = bundler

    async def __call__(self, content: PayloadBundleSource) -> None:
        payloads = self._bundler.bundle(content)

        async def action() -> None:
            await self._swapper.execute(self._scope, payloads)

        await self._run("replace", action, payload={"count": len(payloads)})


class HistoryRebaseOperation(_HistoryOperation):
    """Rebase history markers around a specific message identifier."""

    def __init__(
        self,
        *,
        shifter: RebaseHistoryUseCase,
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
        rewinder: RewindHistoryUseCase,
        guard: Guardian,
        scope,
        reporter: NavigatorReporter,
    ) -> None:
        super().__init__(guard=guard, scope=scope, reporter=reporter)
        self._rewinder = rewinder

    async def __call__(self, context: NavigatorBackContext) -> None:
        handlers = list(context.handler_names())

        async def action() -> None:
            await self._rewinder.execute(self._scope, context)

        await self._run("back", action, handlers=handlers)


class HistoryTrimOperation(_HistoryOperation):
    """Trim history entries with guard orchestration."""

    def __init__(
        self,
        *,
        trimmer: TrimHistoryUseCase,
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


__all__ = [
    "HistoryAddOperation",
    "HistoryBackOperation",
    "HistoryRebaseOperation",
    "HistoryReplaceOperation",
    "HistoryTrimOperation",
]

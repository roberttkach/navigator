"""Restore the previous history entry and re-render when needed."""

from __future__ import annotations

from typing import Any, Awaitable, Callable

from ...core.telemetry import Telemetry
from ...core.value.content import normalize
from ...core.value.message import Scope
from ..log import events
from ..log.aspect import TraceAspect
from .back_access import (
    RewindFinalizer,
    RewindHistoryReader,
    RewindRenderer,
)


class RewindInstrumentation:
    """Isolate tracing concerns from the rewind orchestration."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._trace = TraceAspect(telemetry)

    async def traced(
        self,
        callback: Callable[..., Awaitable[None]],
        *args: Any,
    ) -> None:
        await self._trace.run(events.BACK, callback, *args)


class RewindPerformer:
    """Execute the actual rewind logic without telemetry concerns."""

    def __init__(
        self,
        history: RewindHistoryReader,
        renderer: RewindRenderer,
        finalizer: RewindFinalizer,
    ) -> None:
        self._history = history
        self._renderer = renderer
        self._finalizer = finalizer

    async def perform(self, scope: Scope, context: dict[str, Any]) -> None:
        history = await self._history.snapshot(scope)
        origin, target = self._history.select(history)
        inline = bool(scope.inline)
        memory = await self._history.payload()
        restored = await self._renderer.revive(target, context, memory, inline=inline)
        resolved = [normalize(payload) for payload in restored]
        render = await self._renderer.render(scope, resolved, origin, inline=inline)

        if not render or not getattr(render, "changed", False):
            await self._finalizer.skip(history, target)
            return

        await self._finalizer.apply(history, target, render)


class Rewinder:
    """Coordinate rewind operations for conversation history."""

    def __init__(
        self,
        performer: RewindPerformer,
        instrumentation: RewindInstrumentation,
    ) -> None:
        self._performer = performer
        self._instrumentation = instrumentation

    async def execute(self, scope: Scope, context: dict[str, Any]) -> None:
        """Rewind the history for ``scope`` using extra ``context`` hints."""

        await self._instrumentation.traced(self._performer.perform, scope, context)

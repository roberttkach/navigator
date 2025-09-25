"""Restore the previous history entry and re-render when needed."""

from __future__ import annotations

from typing import Any, Dict

from ..log import events
from ..log.aspect import TraceAspect
from ...core.telemetry import Telemetry
from ...core.value.content import normalize
from ...core.value.message import Scope
from .back_access import (
    RewindFinalizer,
    RewindHistoryAccess,
    RewindMutator,
    RewindRenderer,
)


class Rewinder:
    """Coordinate rewind operations for conversation history."""

    def __init__(
            self,
            history: RewindHistoryAccess,
            renderer: RewindRenderer,
            mutator: RewindMutator,
            telemetry: Telemetry,
            finalizer: RewindFinalizer | None = None,
    ) -> None:
        self._history = history
        self._renderer = renderer
        self._mutator = mutator
        self._finalizer = finalizer or RewindFinalizer(self._history, self._mutator, telemetry)
        self._trace = TraceAspect(telemetry)

    async def execute(self, scope: Scope, context: Dict[str, Any]) -> None:
        """Rewind the history for ``scope`` using extra ``context`` hints."""

        await self._trace.run(events.BACK, self._perform, scope, context)

    async def _perform(self, scope: Scope, context: Dict[str, Any]) -> None:
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

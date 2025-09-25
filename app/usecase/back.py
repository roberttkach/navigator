"""Restore the previous history entry and re-render when needed."""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Sequence

from ..log import events
from ..log.aspect import TraceAspect
from ..service.view.planner import ViewPlanner
from ..service.view.restorer import ViewRestorer
from ...core.entity.history import Entry
from ...core.port.message import MessageGateway
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import normalize
from ...core.value.message import Scope
from .back_access import (
    RewindHistoryAccess,
    RewindMutator,
    RewindRenderer,
    trim,
)


class Rewinder:
    """Coordinate rewind operations for conversation history."""

    def __init__(
            self,
            ledger,
            status,
            gateway: MessageGateway,
            restorer: ViewRestorer,
            planner: ViewPlanner,
            latest,
            telemetry: Telemetry,
            history: RewindHistoryAccess | None = None,
            renderer: RewindRenderer | None = None,
            mutator: RewindMutator | None = None,
    ) -> None:
        self._history = history or RewindHistoryAccess(ledger, status, latest, telemetry)
        self._renderer = renderer or RewindRenderer(restorer, planner)
        self._mutator = mutator or RewindMutator()
        self._gateway = gateway
        self._channel: TelemetryChannel = telemetry.channel(__name__)
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
            await self._handle_skip(history, target)
            return

        rebuilt = self._mutator.rebuild(target, render)
        await self._finalize(history, rebuilt, target, render)

    async def _handle_skip(self, history: Sequence[Entry], target: Entry) -> None:
        """Handle rewind when no rendering changes are required."""

        self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="back")
        await self._history.assign_state(target.state)
        marker = target.messages[0].id if target.messages else None
        await self._history.mark_latest(int(marker) if marker is not None else None)
        await self._history.archive(trim(history))

    async def _finalize(
            self,
            history: Sequence[Entry],
            rebuilt: Entry,
            target: Entry,
            render: Any,
    ) -> None:
        """Persist rebuilt entry and update state/marker telemetry."""

        snapshot = list(trim(history))
        snapshot[-1] = rebuilt
        await self._history.archive(snapshot)
        await self._history.assign_state(target.state)
        identifier = self._mutator.primary_identifier(render)
        await self._history.mark_latest(identifier)

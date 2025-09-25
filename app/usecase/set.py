"""Coordinate state restoration to reconcile history with a desired goal."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any, Dict, List, Optional

from ..log import events
from ..log.aspect import TraceAspect
from ..service.view.planner import RenderNode, ViewPlanner
from ..service.view.restorer import ViewRestorer
from ...core.entity.history import Entry
from ...core.error import StateNotFound
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from ...core.port.message import MessageGateway
from ...core.port.state import StateRepository
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import Payload, normalize
from ...core.value.message import Scope


class Setter:
    """Restore and re-render history entries to satisfy a ``goal`` state."""

    def __init__(
            self,
            ledger: HistoryRepository,
            status: StateRepository,
            gateway: MessageGateway,
            restorer: ViewRestorer,
            planner: ViewPlanner,
            latest: LatestRepository,
            telemetry: Telemetry,
    ):
        self._ledger = ledger
        self._status = status
        self._gateway = gateway
        self._restorer = restorer
        self._planner = planner
        self._latest = latest
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._trace = TraceAspect(telemetry)

    async def execute(
            self,
            scope: Scope,
            goal: str,
            context: Dict[str, Any],
    ) -> None:
        """Restore ``goal`` entry for ``scope`` using additional ``context``."""

        await self._trace.run(events.SET, self._perform, scope, goal, context)

    async def _perform(
            self,
            scope: Scope,
            goal: str,
            context: Dict[str, Any],
    ) -> None:
        """Run the state restoration workflow for ``goal``."""

        history = await self._recall(scope)
        cursor = self._locate(history, goal)
        target = history[cursor]
        inline = bool(scope.inline)
        tail = history[-1] if history else target
        await self._truncate(history, cursor)
        await self._status.assign(target.state)
        self._channel.emit(
            logging.INFO,
            LogCode.STATE_SET,
            op="set",
            state={"target": target.state},
        )
        resolved = await self._revive(target, context, inline)
        render = await self._render(scope, resolved, tail, inline)
        if render and render.changed:
            await self._apply(scope, render)
        else:
            await self._skip(target)

    async def _recall(self, scope: Scope) -> List[Any]:
        """Fetch history for ``scope`` while emitting telemetry."""

        history = await self._ledger.recall()
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="set",
            history={"len": len(history)},
            scope={"chat": scope.chat, "inline": bool(scope.inline)},
        )
        return history

    def _locate(self, history: List[Any], goal: str) -> int:
        """Return the index of the entry whose state matches ``goal``."""

        for index in range(len(history) - 1, -1, -1):
            if history[index].state == goal:
                return index
        raise StateNotFound(goal)

    async def _truncate(self, history: List[Any], cursor: int) -> None:
        """Persist ``history`` truncated to ``cursor`` inclusively."""

        trimmed = history[: cursor + 1]
        await self._archive(trimmed)

    async def _revive(
            self,
            target: Entry,
            context: Dict[str, Any],
            inline: bool,
    ) -> List[Payload]:
        """Return payloads revived from ``target`` merged with ``context``."""

        memory = await self._status.payload()
        if memory is None:
            memory = {}
        merged = {**memory, **context}
        restored = await self._restorer.revive(target, merged, inline=inline)
        return [normalize(p) for p in restored]

    async def _render(
            self,
            scope: Scope,
            resolved: List[Payload],
            tail: Entry,
            inline: bool,
    ) -> Optional[RenderNode]:
        """Render ``resolved`` payloads against ``tail`` context."""

        return await self._planner.render(
            scope,
            resolved,
            tail,
            inline=inline,
        )

    async def _apply(self, scope: Scope, render: RenderNode) -> None:
        """Apply ``render`` metadata to history and refresh markers."""

        current = await self._ledger.recall()
        if current:
            tail = current[-1]
            patched = self._patch(tail, render)
            await self._archive([*current[:-1], patched])
        await self._latest.mark(render.ids[0])
        self._channel.emit(
            logging.INFO,
            LogCode.LAST_SET,
            op="set",
            message={"id": render.ids[0]},
        )

    def _patch(self, entry: Entry, render: RenderNode) -> Entry:
        """Return ``entry`` with identifiers and extras refreshed from ``render``."""

        limit = min(len(entry.messages), len(render.ids))
        messages = list(entry.messages)

        for index in range(limit):
            source = entry.messages[index]
            messages[index] = replace(
                source,
                id=int(render.ids[index]),
                extras=list(render.extras[index]),
            )

        return replace(entry, messages=messages)

    async def _skip(self, target: Entry) -> None:
        """Handle situations where rendering results in no changes."""

        self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="set")
        current = await self._ledger.recall()
        tail = current[-1] if current else target
        if tail.messages:
            await self._latest.mark(tail.messages[0].id)

    async def _archive(self, history: List[Entry]) -> None:
        """Persist ``history`` and emit bookkeeping telemetry."""

        await self._ledger.archive(history)
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op="set",
            history={"len": len(history)},
        )

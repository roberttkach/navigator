"""Supporting components for the state restoration workflow."""
from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from typing import Any, Dict, Iterable, List

from navigator.app.service.view.planner import RenderNode
from navigator.app.service.view.restorer import ViewRestorer
from navigator.core.entity.history import Entry
from navigator.core.error import StateNotFound
from navigator.core.port.history import HistoryRepository
from navigator.core.port.last import LatestRepository
from navigator.core.port.state import StateRepository
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.content import Payload, normalize
from navigator.core.value.message import Scope


@dataclass(frozen=True, slots=True)
class RestorationPlan:
    """Capture the state required to reconcile a requested goal."""

    history: List[Entry]
    target: Entry
    tail: Entry
    cursor: int
    inline: bool


class HistoryRestorationPlanner:
    """Collect history context required for a state restoration run."""

    def __init__(self, ledger: HistoryRepository, telemetry: Telemetry) -> None:
        self._ledger = ledger
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.plan")

    async def build(self, scope: Scope, goal: str) -> RestorationPlan:
        history = await self._ledger.recall()
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="set",
            history={"len": len(history)},
            scope={"chat": scope.chat, "inline": bool(scope.inline)},
        )
        cursor = self._locate(history, goal)
        target = history[cursor]
        tail = history[-1] if history else target
        inline = bool(scope.inline)
        return RestorationPlan(
            history=history,
            target=target,
            tail=tail,
            cursor=cursor,
            inline=inline,
        )

    @staticmethod
    def _locate(history: Iterable[Entry], goal: str) -> int:
        candidates = list(history)
        for index in range(len(candidates) - 1, -1, -1):
            if candidates[index].state == goal:
                return index
        raise StateNotFound(goal)


class StateSynchronizer:
    """Synchronise persistent state assignments with telemetry."""

    def __init__(self, state: StateRepository, telemetry: Telemetry) -> None:
        self._state = state
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.state")

    async def assign(self, entry: Entry) -> None:
        await self._state.assign(entry.state)
        self._channel.emit(
            logging.INFO,
            LogCode.STATE_SET,
            op="set",
            state={"target": entry.state},
        )

    async def snapshot(self) -> Dict[str, Any]:
        memory = await self._state.payload()
        return memory or {}


class PayloadReviver:
    """Merge stored context with fresh data and revive payloads."""

    def __init__(self, synchronizer: StateSynchronizer, restorer: ViewRestorer) -> None:
        self._synchronizer = synchronizer
        self._restorer = restorer

    async def revive(self, entry: Entry, context: Dict[str, Any], *, inline: bool) -> List[Payload]:
        memory = await self._synchronizer.snapshot()
        merged = {**memory, **context}
        restored = await self._restorer.revive(entry, merged, inline=inline)
        return [normalize(payload) for payload in restored]


class HistoryReconciler:
    """Persist render results and telemetry associated with reconciliation."""

    def __init__(
        self,
        ledger: HistoryRepository,
        latest: LatestRepository,
        telemetry: Telemetry,
    ) -> None:
        self._ledger = ledger
        self._latest = latest
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.reconcile")

    async def truncate(self, plan: RestorationPlan) -> None:
        trimmed = plan.history[: plan.cursor + 1]
        await self._ledger.archive(trimmed)

    async def apply(self, scope: Scope, render: RenderNode) -> None:
        current = await self._ledger.recall()
        if current:
            tail = current[-1]
            patched = self._patch(tail, render)
            await self._ledger.archive([*current[:-1], patched])
        await self._latest.mark(render.ids[0])
        self._channel.emit(
            logging.INFO,
            LogCode.LAST_SET,
            op="set",
            message={"id": render.ids[0]},
        )

    async def skip(self) -> None:
        self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="set")

    @staticmethod
    def _patch(entry: Entry, render: RenderNode) -> Entry:
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


__all__ = [
    "HistoryReconciler",
    "HistoryRestorationPlanner",
    "PayloadReviver",
    "RestorationPlan",
    "StateSynchronizer",
]

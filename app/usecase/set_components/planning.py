"""Planning utilities for the state restoration workflow."""
from __future__ import annotations

import logging
from collections.abc import Iterable
from dataclasses import dataclass

from navigator.core.entity.history import Entry
from navigator.core.error import StateNotFound
from navigator.core.port.history import HistoryRepository
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope


@dataclass(frozen=True, slots=True)
class RestorationPlan:
    """Capture the state required to reconcile a requested goal."""

    history: list[Entry]
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


__all__ = ["HistoryRestorationPlanner", "RestorationPlan"]

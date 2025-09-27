"""Tail manipulation helpers used during reconciliation."""
from __future__ import annotations

from dataclasses import replace

from navigator.core.entity.history import Entry
from navigator.core.port.history import HistoryRepository

from ..render_contract import RenderOutcome


class HistoryTailWriter:
    """Handle persistence of history modifications during reconciliation."""

    def __init__(self, ledger: HistoryRepository) -> None:
        self._ledger = ledger

    async def truncate(self, plan: "RestorationPlan") -> None:
        trimmed = plan.history[: plan.cursor + 1]
        await self._ledger.archive(trimmed)

    async def apply(self, render: RenderOutcome) -> None:
        current = await self._ledger.recall()
        if not current:
            return
        tail = current[-1]
        patched = self._patch(tail, render)
        await self._ledger.archive([*current[:-1], patched])

    @staticmethod
    def _patch(entry: Entry, render: RenderOutcome) -> Entry:
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


from .planning import RestorationPlan  # noqa: E402  circular reference for typing

__all__ = ["HistoryTailWriter"]

"""Telemetry-aware readers for tail history repositories."""
from __future__ import annotations

from navigator.core.entity.history import Entry
from navigator.core.value.message import Scope

from .access import TailHistoryAccess
from .journal import TailHistoryJournal


class TailHistoryReader:
    """Expose telemetry-aware read operations for history repositories."""

    def __init__(
        self,
        access: TailHistoryAccess,
        *,
        journal: TailHistoryJournal,
    ) -> None:
        self._access = access
        self._journal = journal

    async def peek(self) -> int | None:
        marker = await self._access.peek()
        self._journal.record_marker_peek(marker)
        return marker

    async def load(self, scope: Scope | None = None) -> list[Entry]:
        snapshot = await self._access.load()
        self._journal.record_history_load(snapshot, scope)
        return snapshot


__all__ = ["TailHistoryReader"]

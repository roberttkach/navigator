"""Telemetry-aware writers for tail history repositories."""
from __future__ import annotations

from collections.abc import Sequence

from navigator.core.entity.history import Entry
from navigator.core.value.message import Scope

from .access import TailHistoryAccess
from .journal import TailHistoryJournal


class TailHistoryWriter:
    """Persist history mutations while recording telemetry."""

    def __init__(
        self,
        access: TailHistoryAccess,
        *,
        journal: TailHistoryJournal,
    ) -> None:
        self._access = access
        self._journal = journal

    async def save(self, history: Sequence[Entry], *, op: str) -> list[Entry]:
        snapshot = await self._access.save(history)
        self._journal.record_history_save(snapshot, op=op)
        return snapshot

    async def mark(
        self,
        marker: int | None,
        *,
        op: str,
        scope: Scope | None = None,
    ) -> None:
        await self._access.mark(marker)
        self._journal.record_marker_mark(marker, op=op, scope=scope)


__all__ = ["TailHistoryWriter"]

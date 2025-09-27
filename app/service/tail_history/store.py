"""Storage primitives for tail history flows."""
from __future__ import annotations

from collections.abc import Sequence

from navigator.core.entity.history import Entry
from navigator.core.port.history import HistoryRepository
from navigator.core.port.last import LatestRepository


class TailHistoryStore:
    """Persist history snapshots and expose latest marker operations."""

    def __init__(self, ledger: HistoryRepository, latest: LatestRepository) -> None:
        self._ledger = ledger
        self._latest = latest

    async def peek(self) -> int | None:
        """Return the most recent marker identifier."""

        return await self._latest.peek()

    async def load(self) -> list[Entry]:
        """Load the persisted history snapshot."""

        return list(await self._ledger.recall())

    async def archive(self, history: Sequence[Entry]) -> list[Entry]:
        """Archive ``history`` and return the stored snapshot."""

        snapshot = list(history)
        await self._ledger.archive(snapshot)
        return snapshot

    async def mark(self, marker: int | None) -> None:
        """Update the latest marker with ``marker`` value."""

        await self._latest.mark(marker)


__all__ = ["TailHistoryStore"]

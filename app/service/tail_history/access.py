"""Access layer composing storage primitives for tail history."""
from __future__ import annotations

from collections.abc import Sequence

from navigator.core.entity.history import Entry
from navigator.core.port.history import HistoryRepository
from navigator.core.port.last import LatestRepository

from .store import TailHistoryStore


class TailHistoryAccess:
    """Provide persistence-only operations for tail history flows."""

    def __init__(
        self,
        ledger: HistoryRepository,
        latest: LatestRepository,
        *,
        store: TailHistoryStore | None = None,
    ) -> None:
        self._store = store or TailHistoryStore(ledger, latest)

    async def peek(self) -> int | None:
        return await self._store.peek()

    async def load(self) -> list[Entry]:
        return await self._store.load()

    async def save(self, history: Sequence[Entry]) -> list[Entry]:
        return await self._store.archive(history)

    async def mark(self, marker: int | None) -> None:
        await self._store.mark(marker)

    @property
    def store(self) -> TailHistoryStore:
        """Expose the underlying store for composition needs."""

        return self._store


__all__ = ["TailHistoryAccess"]

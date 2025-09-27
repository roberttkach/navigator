"""Trimming helpers persisting inline tail history snapshots."""
from __future__ import annotations

from collections.abc import Sequence

from navigator.core.entity.history import Entry

from .marker import TailInlineMarker
from .store import TailHistoryStore


class TailInlineTrimmer:
    """Apply inline-specific trimming rules and persist results."""

    def __init__(
        self,
        store: TailHistoryStore,
        *,
        marker: type[TailInlineMarker] = TailInlineMarker,
    ) -> None:
        self._store = store
        self._marker = marker

    async def trim(self, history: Sequence[Entry]) -> tuple[list[Entry], int | None]:
        trimmed = list(history[:-1])
        stored = await self._store.archive(trimmed)
        marker = self._marker.latest(trimmed)
        await self._store.mark(marker)
        return stored, marker


__all__ = ["TailInlineTrimmer"]

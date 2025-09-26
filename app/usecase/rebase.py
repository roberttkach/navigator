"""Rebase the latest entry marker onto a supplied message identifier."""

from __future__ import annotations

from dataclasses import replace
from typing import List

from ...core.entity.history import Entry
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from .rebase_instrumentation import RebaseInstrumentation


class Shifter:
    """Shift the latest message marker to a newly provided ``marker``."""

    def __init__(
        self,
        ledger: HistoryRepository,
        latest: LatestRepository,
        instrumentation: RebaseInstrumentation,
    ) -> None:
        self._ledger = ledger
        self._latest = latest
        self._instrumentation = instrumentation

    async def execute(self, marker: int) -> None:
        """Rebase history marker onto ``marker`` value."""

        await self._instrumentation.traced(marker, self._perform)

    async def _perform(self, marker: int) -> None:
        history = await self._load_history()
        if not history:
            return

        last = history[-1]
        if not last.messages:
            await self._mark_latest(marker, len(history))
            return

        rebuilt = self._patch_entry(history, last, marker)
        await self._persist(rebuilt, marker)

    async def _load_history(self) -> List[Entry]:
        """Return history snapshots while emitting telemetry."""

        history = await self._ledger.recall()
        self._instrumentation.history_loaded(len(history))
        return history

    async def _mark_latest(self, marker: int, history_len: int) -> None:
        """Update the latest marker and emit success telemetry."""

        identifier = int(marker)
        await self._latest.mark(identifier)
        self._instrumentation.marker_updated(identifier)
        self._instrumentation.completed(identifier, history_len)

    def _patch_entry(self, history: List[Entry], last: Entry, marker: int) -> List[Entry]:
        """Return rebuilt history with ``last`` message id replaced."""

        first = last.messages[0]
        patched = replace(first, id=int(marker))
        trailer = replace(last, messages=[patched, *last.messages[1:]])
        rebuilt: List[Entry] = [*history[:-1], trailer]
        return rebuilt

    async def _persist(self, rebuilt: List[Entry], marker: int) -> None:
        """Persist rebuilt history snapshot and update marker telemetry."""

        await self._ledger.archive(rebuilt)
        self._instrumentation.history_saved(len(rebuilt))
        await self._mark_latest(marker, len(rebuilt))

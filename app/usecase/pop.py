"""Coordinate history trimming while updating telemetry markers."""

from __future__ import annotations

from typing import Sequence

from ...core.entity.history import Entry
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from .pop_instrumentation import PopInstrumentation


class Trimmer:
    """Manage history pop operations with consistent telemetry reporting."""

    def __init__(
        self,
        ledger: HistoryRepository,
        latest: LatestRepository,
        instrumentation: PopInstrumentation,
    ):
        self._ledger = ledger
        self._latest = latest
        self._instrumentation = instrumentation

    async def execute(self, count: int = 1) -> None:
        """Trim history by ``count`` entries while refreshing the latest marker."""

        await self._instrumentation.traced(count, self._perform)

    async def _perform(self, count: int = 1) -> None:
        """Execute the trimming workflow after validating ``count``."""

        if count <= 0:
            self._emit_skip("count_le_0")
            return

        history = await self._recall_history()
        deletions = self._deletions(len(history), count)
        if deletions <= 0:
            return

        trimmed = history[:-deletions]
        await self._persist(trimmed, deletions)

    async def _recall_history(self) -> Sequence[Entry]:
        """Return the current history snapshot with telemetry bookkeeping."""

        history = await self._ledger.recall()
        self._instrumentation.history_loaded(len(history))
        return history

    def _deletions(self, history_len: int, requested: int) -> int:
        """Return the number of entries that should be removed."""

        if history_len <= 1:
            return 0
        return min(requested, history_len - 1)

    async def _persist(self, trimmed: Sequence[Entry], deletions: int) -> None:
        """Persist ``trimmed`` entries and refresh telemetry markers."""

        await self._ledger.archive(list(trimmed))
        self._instrumentation.history_saved(len(trimmed))

        marker = self._latest_marker(trimmed)
        await self._latest.mark(marker)
        self._instrumentation.marker_updated(marker)

        self._instrumentation.completed(deletions, len(trimmed))

    def _latest_marker(self, history: Sequence[Entry]) -> int | None:
        """Return the newest message identifier from ``history`` when present."""

        if not history:
            return None
        messages = history[-1].messages
        if not messages:
            return None
        return int(messages[0].id)

    def _emit_skip(self, note: str) -> None:
        """Record a skip decision with ``note`` for traceability."""

        self._instrumentation.skipped(note)

"""Coordinate history trimming while updating telemetry markers."""

from __future__ import annotations

import logging
from typing import Sequence

from ..log import events
from ..log.aspect import TraceAspect
from ...core.entity.history import Entry
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel


class Trimmer:
    """Manage history pop operations with consistent telemetry reporting."""

    def __init__(self, ledger: HistoryRepository, latest: LatestRepository, telemetry: Telemetry):
        self._ledger = ledger
        self._latest = latest
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._trace = TraceAspect(telemetry)

    async def execute(self, count: int = 1) -> None:
        """Trim history by ``count`` entries while refreshing the latest marker."""

        await self._trace.run(events.POP, self._perform, count)

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
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="pop",
            history={"len": len(history)},
        )
        return history

    def _deletions(self, history_len: int, requested: int) -> int:
        """Return the number of entries that should be removed."""

        if history_len <= 1:
            return 0
        return min(requested, history_len - 1)

    async def _persist(self, trimmed: Sequence[Entry], deletions: int) -> None:
        """Persist ``trimmed`` entries and refresh telemetry markers."""

        await self._ledger.archive(list(trimmed))
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op="pop",
            history={"len": len(trimmed)},
        )

        marker = self._latest_marker(trimmed)
        await self._latest.mark(marker)
        self._channel.emit(
            logging.INFO,
            LogCode.LAST_SET if marker is not None else LogCode.LAST_DELETE,
            op="pop",
            message={"id": marker},
        )

        self._channel.emit(
            logging.INFO,
            LogCode.POP_SUCCESS,
            op="pop",
            history={"len": len(trimmed)},
            note=f"deleted:{deletions}",
        )

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

        self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="pop", note=note)

from __future__ import annotations

import logging

from ..log import events
from ..log.aspect import TraceAspect
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository

class Trimmer:
    def __init__(self, ledger: HistoryRepository, latest: LatestRepository, telemetry: Telemetry):
        self._ledger = ledger
        self._latest = latest
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._trace = TraceAspect(telemetry)

    async def execute(self, count: int = 1) -> None:
        await self._trace.run(events.POP, self._perform, count)

    async def _perform(self, count: int = 1) -> None:
        if count <= 0:
            self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="pop", note="count_le_0")
            return
        history = await self._ledger.recall()
        self._channel.emit(
            logging.DEBUG, LogCode.HISTORY_LOAD, op="pop", history={"len": len(history)}
        )
        if len(history) <= 1:
            return
        limit = min(count, len(history) - 1)
        if limit <= 0:
            return
        trimmed = history[:-limit]
        await self._ledger.archive(trimmed)
        self._channel.emit(
            logging.DEBUG, LogCode.HISTORY_SAVE, op="pop", history={"len": len(trimmed)}
        )

        marker = None
        if trimmed and trimmed[-1].messages:
            marker = int(trimmed[-1].messages[0].id)
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
            note=f"deleted:{limit}",
        )

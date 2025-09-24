from __future__ import annotations

import logging

from ..log.decorators import trace
from navigator.logging import LogCode, jlog
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LatestRepository

logger = logging.getLogger(__name__)


class Trimmer:
    def __init__(self, ledger: HistoryRepository, latest: LatestRepository):
        self._ledger = ledger
        self._latest = latest

    @trace(None, None, None)
    async def execute(self, count: int = 1) -> None:
        if count <= 0:
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="pop", note="count_le_0")
            return
        history = await self._ledger.recall()
        jlog(logger, logging.DEBUG, LogCode.HISTORY_LOAD, op="pop", history={"len": len(history)})
        if len(history) <= 1:
            return
        limit = min(count, len(history) - 1)
        if limit <= 0:
            return
        trimmed = history[:-limit]
        await self._ledger.archive(trimmed)
        jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="pop", history={"len": len(trimmed)})

        marker = None
        if trimmed and trimmed[-1].messages:
            marker = int(trimmed[-1].messages[0].id)
        await self._latest.mark(marker)
        jlog(
            logger,
            logging.INFO,
            LogCode.LAST_SET if marker is not None else LogCode.LAST_DELETE,
            op="pop",
            message={"id": marker},
        )

        jlog(
            logger,
            logging.INFO,
            LogCode.POP_SUCCESS,
            op="pop",
            history={"len": len(trimmed)},
            note=f"deleted:{limit}",
        )

import logging
from typing import List

from ..log.decorators import trace
from ..log.emit import jlog
from ...domain.entity.history import Entry, Message
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LatestRepository
from ...domain.port.temp import TemporaryRepository
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Shifter:
    def __init__(self, ledger: HistoryRepository, buffer: TemporaryRepository,
                 latest: LatestRepository):
        self._ledger = ledger
        self._buffer = buffer
        self._latest = latest

    @trace(None, None, None)
    async def execute(self, marker: int) -> None:
        history = await self._ledger.recall()
        jlog(logger, logging.DEBUG, LogCode.HISTORY_LOAD, op="rebase", history={"len": len(history)})
        if not history:
            return

        last = history[-1]
        if not last.messages:
            await self._buffer.stash([])
            jlog(logger, logging.INFO, LogCode.TEMP_SAVE, op="rebase", temp={"len": 0})
            await self._latest.mark(int(marker))
            jlog(logger, logging.INFO, LogCode.LAST_SET, op="rebase", message={"id": int(marker)})
            jlog(logger, logging.INFO, LogCode.REBASE_SUCCESS, op="rebase",
                 message={"id": int(marker)}, history={"len": len(history)})
            return

        first = last.messages[0]
        patched = Message(
            id=int(marker),
            text=first.text,
            media=first.media,
            group=first.group,
            markup=first.markup,
            preview=first.preview,
            extra=first.extra,
            extras=first.extras,
            inline=first.inline,
            automated=first.automated,
            ts=first.ts,
        )
        trailer = Entry(
            state=last.state,
            view=last.view,
            messages=[patched] + last.messages[1:],
            root=last.root,
        )
        rebuilt: List[Entry] = history[:-1] + [trailer]

        await self._ledger.archive(rebuilt)
        jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="rebase", history={"len": len(rebuilt)})

        await self._buffer.stash([])
        jlog(logger, logging.INFO, LogCode.TEMP_SAVE, op="rebase", temp={"len": 0})

        await self._latest.mark(int(marker))
        jlog(logger, logging.INFO, LogCode.LAST_SET, op="rebase", message={"id": int(marker)})

        jlog(logger, logging.INFO, LogCode.REBASE_SUCCESS, op="rebase",
             message={"id": int(marker)}, history={"len": len(rebuilt)})

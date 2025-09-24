from __future__ import annotations

import logging
from typing import List

from ..log.decorators import trace
from ...core.telemetry import LogCode, telemetry
from ...core.entity.history import Entry, Message
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository

channel = telemetry.channel(__name__)


class Shifter:
    def __init__(self, ledger: HistoryRepository, latest: LatestRepository):
        self._ledger = ledger
        self._latest = latest

    @trace(None, None, None)
    async def execute(self, marker: int) -> None:
        history = await self._ledger.recall()
        channel.emit(logging.DEBUG, LogCode.HISTORY_LOAD, op="rebase", history={"len": len(history)})
        if not history:
            return

        last = history[-1]
        if not last.messages:
            await self._latest.mark(int(marker))
            channel.emit(logging.INFO, LogCode.LAST_SET, op="rebase", message={"id": int(marker)})
            channel.emit(
                logging.INFO,
                LogCode.REBASE_SUCCESS,
                op="rebase",
                message={"id": int(marker)},
                history={"len": len(history)},
            )
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
        channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op="rebase",
            history={"len": len(rebuilt)},
        )

        await self._latest.mark(int(marker))
        channel.emit(logging.INFO, LogCode.LAST_SET, op="rebase", message={"id": int(marker)})

        channel.emit(
            logging.INFO,
            LogCode.REBASE_SUCCESS,
            op="rebase",
            message={"id": int(marker)},
            history={"len": len(rebuilt)},
        )

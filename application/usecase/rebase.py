import logging
from typing import List

from ..log.decorators import log_io
from ..log.emit import jlog
from ...domain.entity.history import Entry, Msg
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LastMessageRepository
from ...domain.port.temp import TemporaryRepository
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Shifter:
    def __init__(self, history_repo: HistoryRepository, temp_repo: TemporaryRepository,
                 last_repo: LastMessageRepository):
        self._history_repo = history_repo
        self._temp_repo = temp_repo
        self._last_repo = last_repo

    @log_io(None, None, None)
    async def execute(self, new_id: int) -> None:
        history = await self._history_repo.get_history()
        jlog(logger, logging.DEBUG, LogCode.HISTORY_LOAD, op="rebase", history={"len": len(history)})
        if not history:
            return

        last = history[-1]
        if not last.messages:
            await self._temp_repo.save_temp_ids([])
            jlog(logger, logging.INFO, LogCode.TEMP_SAVE, op="rebase", temp={"len": 0})
            await self._last_repo.set_last_id(int(new_id))
            jlog(logger, logging.INFO, LogCode.LAST_SET, op="rebase", message={"id": int(new_id)})
            jlog(logger, logging.INFO, LogCode.REBASE_SUCCESS, op="rebase",
                 message={"id": int(new_id)}, history={"len": len(history)})
            return

        first = last.messages[0]
        patched_first = Msg(
            id=int(new_id),
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
        rebased_last = Entry(
            state=last.state,
            view=last.view,
            messages=[patched_first] + last.messages[1:],
            root=last.root,
        )
        rebased: List[Entry] = history[:-1] + [rebased_last]

        await self._history_repo.save_history(rebased)
        jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="rebase", history={"len": len(rebased)})

        await self._temp_repo.save_temp_ids([])
        jlog(logger, logging.INFO, LogCode.TEMP_SAVE, op="rebase", temp={"len": 0})

        await self._last_repo.set_last_id(int(new_id))
        jlog(logger, logging.INFO, LogCode.LAST_SET, op="rebase", message={"id": int(new_id)})

        jlog(logger, logging.INFO, LogCode.REBASE_SUCCESS, op="rebase",
             message={"id": int(new_id)}, history={"len": len(rebased)})

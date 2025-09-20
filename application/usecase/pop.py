import logging

from ..log.decorators import log_io
from ..log.emit import jlog
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LastMessageRepository
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Trimmer:
    def __init__(self, history_repo: HistoryRepository, last_repo: LastMessageRepository):
        self._history_repo = history_repo
        self._last_repo = last_repo

    @log_io(None, None, None)
    async def execute(self, count: int = 1) -> None:
        if count <= 0:
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="pop", note="count_le_0")
            return
        history = await self._history_repo.get_history()
        jlog(logger, logging.DEBUG, LogCode.HISTORY_LOAD, op="pop", history={"len": len(history)})
        if len(history) <= 1:
            return
        num_to_delete = min(count, len(history) - 1)
        if num_to_delete <= 0:
            return
        new_history = history[:-num_to_delete]
        await self._history_repo.save_history(new_history)
        jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="pop", history={"len": len(new_history)})

        new_last_id = None
        if new_history and new_history[-1].messages:
            new_last_id = int(new_history[-1].messages[0].id)
        await self._last_repo.set_last_id(new_last_id)
        jlog(
            logger,
            logging.INFO,
            LogCode.LAST_SET if new_last_id is not None else LogCode.LAST_DELETE,
            op="pop",
            message={"id": new_last_id},
        )

        jlog(
            logger,
            logging.INFO,
            LogCode.POP_SUCCESS,
            op="pop",
            history={"len": len(new_history)},
            note=f"deleted:{num_to_delete}",
        )

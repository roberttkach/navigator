import logging
from typing import List

from aiogram.fsm.context import FSMContext

from .keys import FSM_TEMP_KEY
from ...domain.log.emit import jlog
from ...domain.port.temp import TemporaryRepository
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class TempRepo(TemporaryRepository):
    def __init__(self, state: FSMContext):
        self._state = state

    async def collect(self) -> List[int]:
        data = await self._state.get_data()
        raw = data.get(FSM_TEMP_KEY, [])
        try:
            ids = [int(x) for x in (raw or [])]
        except (TypeError, ValueError):
            ids = []
        jlog(logger, logging.DEBUG, LogCode.TEMP_LOAD, temp={"len": len(ids)})
        return ids

    async def stash(self, ids: List[int]) -> None:
        payload = [int(x) for x in (ids or [])]
        await self._state.update_data({FSM_TEMP_KEY: payload})
        jlog(logger, logging.DEBUG, LogCode.TEMP_SAVE, temp={"len": len(payload)})


__all__ = ["TempRepo"]

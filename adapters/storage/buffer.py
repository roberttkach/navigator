import logging
from typing import List

from aiogram.fsm.context import FSMContext

from .keys import FSM_TEMP_KEY
from ...domain.log.emit import jlog
from ...domain.port.temp import TemporaryRepository
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Buffer(TemporaryRepository):
    def __init__(self, state: FSMContext):
        self._state = state

    async def collect(self) -> List[int]:
        data = await self._state.get_data()
        raw = data.get(FSM_TEMP_KEY, [])
        try:
            identifiers = [int(x) for x in (raw or [])]
        except (TypeError, ValueError):
            identifiers = []
        jlog(logger, logging.DEBUG, LogCode.TEMP_LOAD, temp={"len": len(identifiers)})
        return identifiers

    async def stash(self, identifiers: List[int]) -> None:
        payload = [int(x) for x in (identifiers or [])]
        await self._state.update_data({FSM_TEMP_KEY: payload})
        jlog(logger, logging.DEBUG, LogCode.TEMP_SAVE, temp={"len": len(payload)})

__all__ = ["Buffer"]

from __future__ import annotations

import logging
from typing import Optional

from aiogram.fsm.context import FSMContext

from navigator.domain.port.last import LatestRepository
from navigator.log import LogCode, jlog

from .keys import FSM_LAST_ID_KEY

logger = logging.getLogger(__name__)


class Latest(LatestRepository):
    def __init__(self, state: FSMContext):
        self._state = state

    async def peek(self) -> Optional[int]:
        data = await self._state.get_data()
        marker = data.get(FSM_LAST_ID_KEY)
        jlog(logger, logging.DEBUG, LogCode.LAST_GET, message={"id": marker})
        return marker

    async def mark(self, marker: Optional[int]) -> None:
        await self._state.update_data({FSM_LAST_ID_KEY: marker})
        code = LogCode.LAST_DELETE if marker is None else LogCode.LAST_SET
        jlog(logger, logging.DEBUG, code, message={"id": marker})


__all__ = ["Latest"]

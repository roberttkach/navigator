from __future__ import annotations

import logging
from typing import Optional

from aiogram.fsm.context import FSMContext

from navigator.core.port.last import LatestRepository
from navigator.core.telemetry import LogCode, telemetry

from .keys import FSM_LAST_ID_FIELD, FSM_NAMESPACE_KEY

channel = telemetry.channel(__name__)


class Latest(LatestRepository):
    def __init__(self, state: FSMContext):
        self._state = state

    async def peek(self) -> Optional[int]:
        data = await self._state.get_data()
        namespace = data.get(FSM_NAMESPACE_KEY) or {}
        marker = namespace.get(FSM_LAST_ID_FIELD) if isinstance(namespace, dict) else None
        channel.emit(logging.DEBUG, LogCode.LAST_GET, message={"id": marker})
        return marker

    async def mark(self, marker: Optional[int]) -> None:
        data = await self._state.get_data()
        namespace = dict(data.get(FSM_NAMESPACE_KEY) or {})
        namespace[FSM_LAST_ID_FIELD] = marker
        await self._state.update_data({FSM_NAMESPACE_KEY: namespace})
        code = LogCode.LAST_DELETE if marker is None else LogCode.LAST_SET
        channel.emit(logging.DEBUG, code, message={"id": marker})


__all__ = ["Latest"]

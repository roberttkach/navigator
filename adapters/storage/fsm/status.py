from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from aiogram.fsm.context import FSMContext

from navigator.core.port.state import StateRepository
from navigator.core.telemetry import LogCode, telemetry
from .keys import FSM_NAMESPACE_KEY

channel = telemetry.channel(__name__)


class Status(StateRepository):
    def __init__(self, state: FSMContext):
        self._state = state

    async def status(self) -> Optional[str]:
        current = await self._state.get_state()
        channel.emit(logging.DEBUG, LogCode.STATE_GET, state={"current": current})
        return current

    async def assign(self, state: Optional[str]) -> None:
        await self._state.set_state(state)
        channel.emit(logging.DEBUG, LogCode.STATE_SET, state={"target": state})

    async def payload(self) -> Dict[str, Any]:
        mapping = await self._state.get_data()
        filtered = {key: value for key, value in mapping.items() if key != FSM_NAMESPACE_KEY}
        count = len(filtered)
        channel.emit(logging.DEBUG, LogCode.STATE_DATA_GET, data={"keys": count})
        return filtered


__all__ = ["Status"]

from __future__ import annotations

import logging
from aiogram.fsm.context import FSMContext
from navigator.core.port.state import StateRepository
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from typing import Any, Dict, Optional

from .keys import FSM_NAMESPACE_KEY


class Status(StateRepository):
    def __init__(self, state: FSMContext, telemetry: Telemetry | None = None):
        self._state = state
        self._channel: TelemetryChannel | None = (
            telemetry.channel(__name__) if telemetry else None
        )

    def _emit(self, level: int, code: LogCode, /, **fields: Any) -> None:
        if self._channel:
            self._channel.emit(level, code, **fields)

    async def status(self) -> Optional[str]:
        current = await self._state.get_state()
        self._emit(logging.DEBUG, LogCode.STATE_GET, state={"current": current})
        return current

    async def assign(self, state: Optional[str]) -> None:
        await self._state.set_state(state)
        self._emit(logging.DEBUG, LogCode.STATE_SET, state={"target": state})

    async def payload(self) -> Dict[str, Any]:
        mapping = await self._state.get_data()
        filtered = {key: value for key, value in mapping.items() if key != FSM_NAMESPACE_KEY}
        count = len(filtered)
        self._emit(logging.DEBUG, LogCode.STATE_DATA_GET, data={"keys": count})
        return filtered


__all__ = ["Status"]

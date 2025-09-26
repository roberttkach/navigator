from __future__ import annotations

import logging
from navigator.core.port.last import LatestRepository
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from typing import Optional

from .keys import FSM_LAST_ID_FIELD, FSM_NAMESPACE_KEY
from .context import StateContext


class Latest(LatestRepository):
    def __init__(self, state: StateContext, telemetry: Telemetry | None = None):
        self._state = state
        self._channel: TelemetryChannel | None = (
            telemetry.channel(__name__) if telemetry else None
        )

    def _emit(self, level: int, code: LogCode, /, **fields: object) -> None:
        if self._channel:
            self._channel.emit(level, code, **fields)

    async def peek(self) -> Optional[int]:
        data = await self._state.get_data()
        namespace = data.get(FSM_NAMESPACE_KEY) or {}
        marker = namespace.get(FSM_LAST_ID_FIELD) if isinstance(namespace, dict) else None
        self._emit(logging.DEBUG, LogCode.LAST_GET, message={"id": marker})
        return marker

    async def mark(self, marker: Optional[int]) -> None:
        data = await self._state.get_data()
        namespace = dict(data.get(FSM_NAMESPACE_KEY) or {})
        namespace[FSM_LAST_ID_FIELD] = marker
        await self._state.update_data({FSM_NAMESPACE_KEY: namespace})
        code = LogCode.LAST_DELETE if marker is None else LogCode.LAST_SET
        self._emit(logging.DEBUG, code, message={"id": marker})


__all__ = ["Latest"]

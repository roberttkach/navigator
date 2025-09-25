from __future__ import annotations

import asyncio
import logging
from typing import List

from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.ids import order as _order
from navigator.core.value.message import Scope

from ..errors import excusable
from .retry import invoke

class DeleteBatch:
    def __init__(self, bot, *, chunk: int, delay: float, telemetry: Telemetry) -> None:
        self._bot = bot
        size = int(chunk)
        self._chunk = max(min(size, 100), 1)
        self._delay = max(float(delay), 0.0)
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def run(self, scope: Scope, identifiers: List[int]) -> None:
        if scope.inline and not scope.business:
            self._channel.emit(
                logging.INFO,
                LogCode.RENDER_SKIP,
                scope=profile(scope),
                note="inline_without_business_delete_skip",
                count=len(identifiers or []),
            )
            return
        if not identifiers:
            return
        unique = _order(identifiers)
        if not unique:
            return
        groups = [
            unique[start:start + self._chunk]
            for start in range(0, len(unique), self._chunk)
        ]
        total = len(groups)
        self._channel.emit(
            logging.DEBUG,
            LogCode.RERENDER_START,
            note="delete_chunking",
            count=len(unique),
            chunks=total,
            chunk=self._chunk,
        )
        scopeview = profile(scope)
        if scope.business:
            eraser = self._bot.delete_business_messages
            params = {"business_connection_id": scope.business}
        else:
            eraser = self._bot.delete_messages
            params = {"chat_id": scope.chat}
        try:
            for index, group in enumerate(groups, start=1):
                try:
                    await invoke(
                        eraser,
                        message_ids=group,
                        **params,
                        channel=self._channel,
                    )
                    self._channel.emit(
                        logging.INFO,
                        LogCode.GATEWAY_DELETE_OK,
                        scope=scopeview,
                        message={"deleted": len(group)},
                        chunk={"index": index, "total": total},
                    )
                    if self._delay:
                        await asyncio.sleep(self._delay)
                except Exception as error:
                    if excusable(error):
                        continue
                    raise
        except Exception as error:
            self._channel.emit(
                logging.WARNING,
                LogCode.GATEWAY_DELETE_FAIL,
                scope=scopeview,
                count=len(unique),
                note=type(error).__name__,
            )
            raise

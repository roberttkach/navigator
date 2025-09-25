from __future__ import annotations

import asyncio
import logging
from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.ids import order as arrange
from navigator.core.value.message import Scope
from typing import List

from .retry import invoke
from ..errors import excusable


class PurgeTask:
    def __init__(self, bot, *, chunk: int, delay: float, telemetry: Telemetry) -> None:
        self._bot = bot
        size = int(chunk)
        self._chunk = max(min(size, 100), 1)
        self._delay = max(float(delay), 0.0)
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def execute(self, scope: Scope, identifiers: List[int]) -> None:
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
        unique = arrange(identifiers)
        if not unique:
            return
        batches = [
            unique[start:start + self._chunk]
            for start in range(0, len(unique), self._chunk)
        ]
        total = len(batches)
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
            eraser = getattr(self._bot, "delete_business_messages", None)
            params = {"business_connection_id": scope.business}
        else:
            eraser = getattr(self._bot, "delete_messages", None)
            params = {"chat_id": scope.chat}
        try:
            for index, batch in enumerate(batches, start=1):
                try:
                    if eraser is not None:
                        await invoke(
                            eraser,
                            message_ids=batch,
                            **params,
                            channel=self._channel,
                        )
                    else:
                        # Fallback to singles (non-business only)
                        if scope.business:
                            raise RuntimeError("bulk_business_delete_unsupported")
                        for mid in batch:
                            await invoke(
                                self._bot.delete_message,
                                chat_id=scope.chat,
                                message_id=mid,
                                channel=self._channel,
                            )
                    self._channel.emit(
                        logging.INFO,
                        LogCode.GATEWAY_DELETE_OK,
                        scope=scopeview,
                        message={"deleted": len(batch)},
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

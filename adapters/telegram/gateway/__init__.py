from __future__ import annotations

import logging
from typing import List

from aiogram import Bot

from .delete import DeleteBatch
from .edit import rewrite, recast, retitle, remap
from .send import dispatch
from .util import targets
from ....domain.error import InlineUnsupported
from ....domain.log.emit import jlog
from ....domain.port.markup import MarkupCodec
from ....domain.port.message import MessageGateway, Result
from ....domain.service.scope import profile
from ....domain.value.content import Payload
from ....domain.value.message import Scope
from ....domain.log.code import LogCode

logger = logging.getLogger(__name__)


class TelegramGateway(MessageGateway):
    def __init__(self, bot: Bot, codec: MarkupCodec, chunk: int = 100, truncate: bool = False):
        self._bot = bot
        self._codec = codec
        self._chunk = int(chunk)
        self._truncate = bool(truncate)

    async def send(self, scope: Scope, payload: Payload) -> Result:
        if scope.inline:
            raise InlineUnsupported("inline_send_not_supported")
        return await dispatch(self._bot, self._codec, scope, payload, truncate=self._truncate)

    async def rewrite(self, scope: Scope, message: int, payload: Payload) -> Result:
        return await rewrite(self._bot, self._codec, scope, message, payload, truncate=self._truncate)

    async def recast(self, scope: Scope, message: int, payload: Payload) -> Result:
        return await recast(self._bot, self._codec, scope, message, payload, truncate=self._truncate)

    async def retitle(self, scope: Scope, message: int, payload: Payload) -> Result:
        return await retitle(self._bot, self._codec, scope, message, payload, truncate=self._truncate)

    async def remap(self, scope: Scope, message: int, payload: Payload) -> Result:
        return await remap(self._bot, self._codec, scope, message, payload)

    async def delete(self, scope: Scope, identifiers: List[int]) -> None:
        runner = DeleteBatch(bot=self._bot, chunk=self._chunk)
        await runner.run(scope, identifiers)

    async def alert(self, scope: Scope, text: str) -> None:
        if scope.inline or not text:
            return
        kwargs = targets(scope)
        await self._bot.send_message(
            text=text,
            **kwargs,
        )
        jlog(
            logger,
            logging.INFO,
            LogCode.GATEWAY_NOTIFY_EMPTY,
            scope=profile(scope),
        )


__all__ = ["TelegramGateway"]

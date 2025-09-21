from __future__ import annotations

import logging
from typing import List

from aiogram import Bot

from .delete import BatchDeleteRunner
from .edit import do_edit_text, do_edit_media, do_edit_caption, do_edit_markup
from .send import do_send
from .util import targets
from ....domain.error import InlineUnsupported
from ....domain.log.emit import jlog
from ....domain.port.markup import MarkupCodec
from ....domain.port.message import MessageGateway, Result
from ....domain.service.scope import profile
from ....domain.value.content import Payload
from ....presentation.telegram.lexicon import lexeme
from ....domain.value.message import Scope
from ....domain.log.code import LogCode

logger = logging.getLogger(__name__)


class TelegramGateway(MessageGateway):
    def __init__(self, bot: Bot, markup_codec: MarkupCodec, chunk_size: int = 100, truncate: bool = False):
        self._bot = bot
        self._codec = markup_codec
        self._chunk_size = int(chunk_size)
        self._truncate = bool(truncate)

    async def send(self, scope: Scope, payload: Payload) -> Result:
        if scope.inline:
            raise InlineUnsupported("inline_send_not_supported")
        return await do_send(self._bot, self._codec, scope, payload, truncate=self._truncate)

    async def edit_text(self, scope: Scope, message_id: int, payload: Payload) -> Result:
        return await do_edit_text(self._bot, self._codec, scope, message_id, payload, truncate=self._truncate)

    async def edit_media(self, scope: Scope, message_id: int, payload: Payload) -> Result:
        return await do_edit_media(self._bot, self._codec, scope, message_id, payload, truncate=self._truncate)

    async def edit_caption(self, scope: Scope, message_id: int, payload: Payload) -> Result:
        return await do_edit_caption(self._bot, self._codec, scope, message_id, payload, truncate=self._truncate)

    async def edit_markup(self, scope: Scope, message_id: int, payload: Payload) -> Result:
        return await do_edit_markup(self._bot, self._codec, scope, message_id, payload)

    async def delete(self, scope: Scope, ids: List[int]) -> None:
        runner = BatchDeleteRunner(bot=self._bot, chunk_size=self._chunk_size)
        await runner.run(scope, ids)

    async def alert(self, scope: Scope) -> None:
        if not scope.inline:
            kwargs = targets(scope)
            await self._bot.send_message(
                text=lexeme("prev_not_found", scope.lang or "en"),
                **kwargs,
            )
            jlog(
                logger,
                logging.INFO,
                LogCode.GATEWAY_NOTIFY_EMPTY,
                scope=profile(scope),
            )


__all__ = ["TelegramGateway"]

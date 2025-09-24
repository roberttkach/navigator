from __future__ import annotations

import logging
from typing import List

from aiogram import Bot

from navigator.log import LogCode, jlog
from navigator.domain.port.extraschema import ExtraSchema
from navigator.domain.port.limits import Limits
from navigator.domain.port.markup import MarkupCodec
from navigator.domain.port.message import MessageGateway, Result
from navigator.domain.port.pathpolicy import MediaPathPolicy
from navigator.domain.port.preview import LinkPreviewCodec
from navigator.domain.service.scope import profile
from navigator.domain.value.content import Payload
from navigator.domain.value.message import Scope

from ..serializer.screen import SignatureScreen
from . import util
from .edit import recast, remap, retitle, rewrite
from .send import send

logger = logging.getLogger(__name__)


class TelegramGateway(MessageGateway):
    def __init__(
        self,
        bot: Bot,
        *,
        codec: MarkupCodec,
        limits: Limits,
        schema: ExtraSchema,
        policy: MediaPathPolicy,
        screen: SignatureScreen,
        preview: LinkPreviewCodec | None = None,
        chunk: int = 100,
        truncate: bool = False,
        delete_delay: float = 0.05,
    ) -> None:
        self._bot = bot
        self._codec = codec
        self._limits = limits
        self._schema = schema
        self._policy = policy
        self._screen = screen
        self._preview = preview
        self._truncate = truncate
        from .delete import DeleteBatch

        self._delete = DeleteBatch(bot, chunk=chunk, delay=delete_delay)

    async def send(self, scope: Scope, payload: Payload) -> Result:
        message, extras, meta = await send(
            self._bot,
            codec=self._codec,
            schema=self._schema,
            screen=self._screen,
            policy=self._policy,
            limits=self._limits,
            preview=self._preview,
            scope=scope,
            payload=payload,
            truncate=self._truncate,
        )
        return Result(id=message.message_id, extra=extras, **meta)

    async def rewrite(self, scope: Scope, message: int, payload: Payload) -> Result:
        outcome = await rewrite(
            self._bot,
            codec=self._codec,
            schema=self._schema,
            screen=self._screen,
            limits=self._limits,
            preview=self._preview,
            scope=scope,
            message_id=message,
            payload=payload,
            truncate=self._truncate,
        )
        meta = util.extract(outcome, payload, scope)
        identifier = getattr(outcome, "message_id", message)
        return Result(id=identifier, extra=[], **meta)

    async def recast(self, scope: Scope, message: int, payload: Payload) -> Result:
        outcome = await recast(
            self._bot,
            codec=self._codec,
            schema=self._schema,
            screen=self._screen,
            policy=self._policy,
            limits=self._limits,
            scope=scope,
            message_id=message,
            payload=payload,
            truncate=self._truncate,
        )
        meta = util.extract(outcome, payload, scope)
        identifier = getattr(outcome, "message_id", message)
        return Result(id=identifier, extra=[], **meta)

    async def retitle(self, scope: Scope, message: int, payload: Payload) -> Result:
        outcome = await retitle(
            self._bot,
            codec=self._codec,
            schema=self._schema,
            screen=self._screen,
            limits=self._limits,
            scope=scope,
            message_id=message,
            payload=payload,
            truncate=self._truncate,
        )
        meta = util.extract(outcome, payload, scope)
        identifier = getattr(outcome, "message_id", message)
        return Result(id=identifier, extra=[], **meta)

    async def remap(self, scope: Scope, message: int, payload: Payload) -> Result:
        outcome = await remap(
            self._bot,
            codec=self._codec,
            scope=scope,
            message_id=message,
            payload=payload,
        )
        meta = util.extract(outcome, payload, scope)
        identifier = getattr(outcome, "message_id", message)
        return Result(id=identifier, extra=[], **meta)

    async def delete(self, scope: Scope, identifiers: List[int]) -> None:
        await self._delete.run(scope, identifiers)

    async def alert(self, scope: Scope, text: str) -> None:
        if scope.inline or not text:
            return
        kwargs = util.targets(scope)
        await self._bot.send_message(text=text, **kwargs)
        jlog(
            logger,
            logging.INFO,
            LogCode.GATEWAY_NOTIFY_OK,
            scope=profile(scope),
        )


__all__ = ["TelegramGateway"]

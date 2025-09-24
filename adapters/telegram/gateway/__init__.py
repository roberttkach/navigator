from __future__ import annotations
from __future__ import annotations

import logging
from typing import List

from aiogram import Bot

from domain.log.code import LogCode
from domain.log.emit import jlog
from domain.port.extraschema import ExtraSchema
from domain.port.limits import Limits
from domain.port.markup import MarkupCodec
from domain.port.message import MessageGateway, Result
from domain.port.pathpolicy import MediaPathPolicy
from domain.service.scope import profile
from domain.value.content import Payload
from domain.value.message import Scope

from ..serializer.screen import SignatureScreen
from . import util
from .delete import DeleteBatch
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
        self._truncate = truncate
        self._delete = DeleteBatch(bot, chunk=chunk, delay=delete_delay)

    async def send(self, scope: Scope, payload: Payload) -> Result:
        message, extras, meta = await send(
            self._bot,
            codec=self._codec,
            schema=self._schema,
            screen=self._screen,
            policy=self._policy,
            limits=self._limits,
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
            LogCode.GATEWAY_NOTIFY_EMPTY,
            scope=profile(scope),
        )


__all__ = ["TelegramGateway"]

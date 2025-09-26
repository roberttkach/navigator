from __future__ import annotations

import logging
from typing import Callable, List

from aiogram import Bot

from navigator.core.port.extraschema import ExtraSchema
from navigator.core.port.limits import Limits
from navigator.core.port.markup import MarkupCodec
from navigator.core.port.message import MessageGateway, Result
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.port.preview import LinkPreviewCodec
from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from . import util
from .edit import recast, remap, retitle, rewrite
from .purge import PurgeTask
from .send import send
from ..serializer.screen import SignatureScreen


class TelegramMessageTransport:
    """Handle Telegram message send and edit operations."""

    def __init__(
        self,
        bot: Bot,
        *,
        codec: MarkupCodec,
        limits: Limits,
        schema: ExtraSchema,
        policy: MediaPathPolicy,
        screen: SignatureScreen,
        preview: LinkPreviewCodec | None,
        truncate: bool,
        telemetry: Telemetry,
    ) -> None:
        self._bot = bot
        self._codec = codec
        self._limits = limits
        self._schema = schema
        self._policy = policy
        self._screen = screen
        self._preview = preview
        self._truncate = truncate
        self._telemetry = telemetry
        self._channel: TelemetryChannel = telemetry.channel(__name__)

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
            channel=self._channel,
            telemetry=self._telemetry,
        )
        return Result(id=message.message_id, extra=extras, meta=meta)

    async def rewrite(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        outcome = await rewrite(
            self._bot,
            codec=self._codec,
            schema=self._schema,
            screen=self._screen,
            limits=self._limits,
            preview=self._preview,
            scope=scope,
            identifier=identifier,
            payload=payload,
            truncate=self._truncate,
            channel=self._channel,
        )
        meta = util.extract(outcome, payload, scope)
        resultid = getattr(outcome, "message_id", identifier)
        return Result(id=resultid, extra=[], meta=meta)

    async def recast(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        outcome = await recast(
            self._bot,
            codec=self._codec,
            schema=self._schema,
            screen=self._screen,
            policy=self._policy,
            limits=self._limits,
            scope=scope,
            identifier=identifier,
            payload=payload,
            truncate=self._truncate,
            channel=self._channel,
        )
        meta = util.extract(outcome, payload, scope)
        resultid = getattr(outcome, "message_id", identifier)
        return Result(id=resultid, extra=[], meta=meta)

    async def retitle(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        outcome = await retitle(
            self._bot,
            codec=self._codec,
            schema=self._schema,
            screen=self._screen,
            limits=self._limits,
            scope=scope,
            identifier=identifier,
            payload=payload,
            truncate=self._truncate,
            channel=self._channel,
        )
        meta = util.extract(outcome, payload, scope)
        resultid = getattr(outcome, "message_id", identifier)
        return Result(id=resultid, extra=[], meta=meta)

    async def remap(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        outcome = await remap(
            self._bot,
            codec=self._codec,
            scope=scope,
            identifier=identifier,
            payload=payload,
            channel=self._channel,
        )
        meta = util.extract(outcome, payload, scope)
        resultid = getattr(outcome, "message_id", identifier)
        return Result(id=resultid, extra=[], meta=meta)


class TelegramDeletionManager:
    """Coordinate message purge operations for Telegram gateway."""

    def __init__(self, bot: Bot, *, chunk: int, delay: float, telemetry: Telemetry) -> None:
        self._task = PurgeTask(bot, chunk=chunk, delay=delay, telemetry=telemetry)

    async def delete(self, scope: Scope, identifiers: List[int]) -> None:
        await self._task.execute(scope, identifiers)


class TelegramNotifier:
    """Emit notifications to Telegram chats and record telemetry."""

    def __init__(self, bot: Bot, *, telemetry: Telemetry) -> None:
        self._bot = bot
        self._channel = telemetry.channel(__name__)

    async def alert(self, scope: Scope, text: str) -> None:
        if scope.inline or not text:
            return
        kwargs = util.targets(scope)
        await self._bot.send_message(text=text, **kwargs)
        self._channel.emit(
            logging.INFO,
            LogCode.GATEWAY_NOTIFY_OK,
            scope=profile(scope),
        )


class TelegramGateway(MessageGateway):
    """Facade delegating Telegram operations to dedicated collaborators."""

    def __init__(
        self,
        *,
        transport: TelegramMessageTransport,
        deletion: TelegramDeletionManager,
        notifier: TelegramNotifier,
    ) -> None:
        self._transport = transport
        self._deletion = deletion
        self._notifier = notifier

    async def send(self, scope: Scope, payload: Payload) -> Result:
        return await self._transport.send(scope, payload)

    async def rewrite(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        return await self._transport.rewrite(scope, identifier, payload)

    async def recast(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        return await self._transport.recast(scope, identifier, payload)

    async def retitle(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        return await self._transport.retitle(scope, identifier, payload)

    async def remap(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        return await self._transport.remap(scope, identifier, payload)

    async def delete(self, scope: Scope, identifiers: List[int]) -> None:
        await self._deletion.delete(scope, identifiers)

    async def alert(self, scope: Scope, text: str) -> None:
        await self._notifier.alert(scope, text)


def create_gateway(
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
    deletepause: float = 0.05,
    telemetry: Telemetry,
    transport_factory: Callable[..., TelegramMessageTransport] = TelegramMessageTransport,
    deletion_factory: Callable[..., TelegramDeletionManager] = TelegramDeletionManager,
    notifier_factory: Callable[..., TelegramNotifier] = TelegramNotifier,
) -> TelegramGateway:
    transport = transport_factory(
        bot,
        codec=codec,
        limits=limits,
        schema=schema,
        policy=policy,
        screen=screen,
        preview=preview,
        truncate=truncate,
        telemetry=telemetry,
    )
    deletion = deletion_factory(
        bot,
        chunk=chunk,
        delay=deletepause,
        telemetry=telemetry,
    )
    notifier = notifier_factory(bot, telemetry=telemetry)
    return TelegramGateway(
        transport=transport,
        deletion=deletion,
        notifier=notifier,
    )


__all__ = ["TelegramGateway", "create_gateway"]

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
from .send import SendContextFactory, SendDispatcher
from ..serializer.screen import SignatureScreen


def _message_result(
    outcome: object,
    identifier: int,
    payload: Payload,
    scope: Scope,
) -> Result:
    meta = util.extract(outcome, payload, scope)
    result_id = getattr(outcome, "message_id", identifier)
    return Result(id=result_id, extra=[], meta=meta)


class TelegramMessageSender:
    """Coordinate Telegram send operations for navigator payloads."""

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
        self._dispatcher = SendDispatcher(
            bot,
            schema=schema,
            screen=screen,
            policy=policy,
            limits=limits,
            telemetry=telemetry,
        )
        self._context_factory = SendContextFactory(codec=codec, preview=preview)
        self._truncate = truncate
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def send(self, scope: Scope, payload: Payload) -> Result:
        context = self._context_factory.build(scope=scope, payload=payload, channel=self._channel)
        message, extras, meta = await self._dispatcher.dispatch(
            payload,
            scope=scope,
            context=context,
            truncate=self._truncate,
        )
        return Result(id=message.message_id, extra=extras, meta=meta)


class TelegramMessageEditor:
    """Handle Telegram edit operations using dedicated helpers."""

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
        self._channel: TelemetryChannel = telemetry.channel(__name__)

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
        return _message_result(outcome, identifier, payload, scope)

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
        return _message_result(outcome, identifier, payload, scope)

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
        return _message_result(outcome, identifier, payload, scope)


class TelegramMarkupRefiner:
    """Manage reply markup remapping for Telegram messages."""

    def __init__(
        self,
        bot: Bot,
        *,
        codec: MarkupCodec,
        telemetry: Telemetry,
    ) -> None:
        self._bot = bot
        self._codec = codec
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def remap(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        outcome = await remap(
            self._bot,
            codec=self._codec,
            scope=scope,
            identifier=identifier,
            payload=payload,
            channel=self._channel,
        )
        return _message_result(outcome, identifier, payload, scope)


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
        sender: TelegramMessageSender,
        editor: TelegramMessageEditor,
        markup: TelegramMarkupRefiner,
        deletion: TelegramDeletionManager,
        notifier: TelegramNotifier,
    ) -> None:
        self._sender = sender
        self._editor = editor
        self._markup = markup
        self._deletion = deletion
        self._notifier = notifier

    async def send(self, scope: Scope, payload: Payload) -> Result:
        return await self._sender.send(scope, payload)

    async def rewrite(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        return await self._editor.rewrite(scope, identifier, payload)

    async def recast(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        return await self._editor.recast(scope, identifier, payload)

    async def retitle(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        return await self._editor.retitle(scope, identifier, payload)

    async def remap(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        return await self._markup.remap(scope, identifier, payload)

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
    sender_factory: Callable[..., TelegramMessageSender] = TelegramMessageSender,
    editor_factory: Callable[..., TelegramMessageEditor] = TelegramMessageEditor,
    markup_factory: Callable[..., TelegramMarkupRefiner] = TelegramMarkupRefiner,
    deletion_factory: Callable[..., TelegramDeletionManager] = TelegramDeletionManager,
    notifier_factory: Callable[..., TelegramNotifier] = TelegramNotifier,
) -> TelegramGateway:
    sender = sender_factory(
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
    editor = editor_factory(
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
    markup = markup_factory(
        bot,
        codec=codec,
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
        sender=sender,
        editor=editor,
        markup=markup,
        deletion=deletion,
        notifier=notifier,
    )


__all__ = [
    "TelegramGateway",
    "TelegramMessageEditor",
    "TelegramMessageSender",
    "TelegramMarkupRefiner",
    "create_gateway",
]

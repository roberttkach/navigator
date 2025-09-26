"""Composable helpers orchestrating Telegram send operations."""
from __future__ import annotations

from aiogram import Bot
from aiogram.types import Message

from navigator.core.port.extraschema import ExtraSchema
from navigator.core.port.markup import MarkupCodec
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.port.preview import LinkPreviewCodec
from navigator.core.port.limits import Limits
from navigator.core.telemetry import Telemetry, TelemetryChannel
from navigator.core.typing.result import Meta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ..serializer.screen import SignatureScreen

from .context import SendContextFactory
from .dependencies import SendDependencies
from .dispatcher import SendDispatcher
from .factory import SendDispatcherFactory


async def send(
    bot: Bot,
    *,
    codec: MarkupCodec,
    schema: ExtraSchema,
    screen: SignatureScreen,
    policy: MediaPathPolicy,
    limits: Limits,
    preview: LinkPreviewCodec | None,
    scope: Scope,
    payload: Payload,
    truncate: bool,
    channel: TelemetryChannel,
    telemetry: Telemetry,
) -> tuple[Message, list[int], Meta]:
    dependencies = SendDependencies(
        schema=schema,
        screen=screen,
        policy=policy,
        limits=limits,
        telemetry=telemetry,
    )
    dispatcher = SendDispatcherFactory(dependencies).create(bot)
    context_factory = SendContextFactory(codec=codec, preview=preview)
    context = context_factory.build(scope=scope, payload=payload, channel=channel)
    return await dispatcher.dispatch(
        payload,
        scope=scope,
        context=context,
        truncate=truncate,
    )


__all__ = [
    "SendContextFactory",
    "SendDependencies",
    "SendDispatcher",
    "SendDispatcherFactory",
    "send",
]

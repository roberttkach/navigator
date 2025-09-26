"""Factory helpers creating Telegram gateway instances."""
from __future__ import annotations

from collections.abc import Callable

from aiogram import Bot

from navigator.core.port.extraschema import ExtraSchema
from navigator.core.port.limits import Limits
from navigator.core.port.markup import MarkupCodec
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.port.preview import LinkPreviewCodec
from navigator.core.telemetry import Telemetry

from ..serializer.screen import SignatureScreen
from .deletion import TelegramDeletionManager
from .gateway import TelegramGateway
from .markup import TelegramMarkupRefiner
from .notifier import TelegramNotifier
from .sender import TelegramMessageSender
from .editor import TelegramMessageEditor


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


__all__ = ["create_gateway"]

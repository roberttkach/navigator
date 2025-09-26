"""Concrete send strategies for Telegram payload types."""
from __future__ import annotations

from typing import Dict

from aiogram import Bot
from aiogram.types import Message
from navigator.core.typing.result import GroupMeta, Meta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ..media import assemble
from ..serializer import caption as captionkit
from ..serializer.screen import SignatureScreen
from .. import util

from .context import SendContext
from .dependencies import SendDependencies
from .guardian import LimitsGuardian
from .clusters import GroupClusterBuilder


class AlbumSender:
    """Send album payloads via Telegram bot API."""

    def __init__(self, dependencies: SendDependencies) -> None:
        self._schema = dependencies.schema
        self._screen = dependencies.screen
        self._policy = dependencies.policy
        self._limits = dependencies.limits
        self._telemetry = dependencies.telemetry
        self._clusters = GroupClusterBuilder()

    async def send(
        self,
        bot: Bot,
        payload: Payload,
        *,
        scope: Scope,
        context: SendContext,
    ) -> tuple[Message, list[int], GroupMeta]:
        caption = captionkit.caption(payload)
        extras = self._schema.send(scope, payload.extra, span=len(caption or ""), media=True)
        bundle = assemble(
            payload.group,
            captionmeta=extras.get("caption", {}),
            mediameta=extras.get("media", {}),
            policy=self._policy,
            screen=self._screen,
            limits=self._limits,
            native=True,
            telemetry=self._telemetry,
        )
        effect = extras.get("effect")
        addition: Dict[str, object] = {}
        if effect is not None:
            addition = self._screen.filter(
                bot.send_media_group,
                {"message_effect_id": effect},
            )

        messages = await bot.send_media_group(
            media=bundle,
            **context.targets,
            **addition,
        )
        head = messages[0]
        context.reporter.success(head.message_id, len(messages) - 1)
        meta = GroupMeta(
            clusters=self._clusters.build(messages, payload),
            inline=scope.inline,
        )
        extras_ids = [message.message_id for message in messages[1:]]
        return head, extras_ids, meta


class SingleMediaSender:
    """Send single media payloads."""

    def __init__(self, dependencies: SendDependencies, guard: LimitsGuardian) -> None:
        self._schema = dependencies.schema
        self._screen = dependencies.screen
        self._policy = dependencies.policy
        self._guard = guard

    async def send(
        self,
        bot: Bot,
        payload: Payload,
        *,
        scope: Scope,
        context: SendContext,
        truncate: bool,
    ) -> tuple[Message, list[int], Meta]:
        caption = captionkit.caption(payload)
        caption = self._guard.caption(caption, truncate, context.reporter)
        extras = self._schema.send(scope, payload.extra, span=len(caption or ""), media=True)
        sender = getattr(bot, f"send_{payload.media.type.value}")
        arguments = {
            **context.targets,
            payload.media.type.value: self._policy.adapt(payload.media.path, native=True),
            "reply_markup": context.markup,
        }
        if caption is not None:
            arguments["caption"] = caption
        arguments.update(self._screen.filter(sender, extras.get("caption", {})))
        arguments.update(self._screen.filter(sender, extras.get("media", {})))
        message = await sender(**arguments)
        context.reporter.success(message.message_id, 0)
        meta = util.extract(message, payload, scope)
        return message, [], meta


class TextSender:
    """Send plain text payloads."""

    def __init__(self, dependencies: SendDependencies, guard: LimitsGuardian) -> None:
        self._schema = dependencies.schema
        self._screen = dependencies.screen
        self._guard = guard

    async def send(
        self,
        bot: Bot,
        payload: Payload,
        *,
        scope: Scope,
        context: SendContext,
        truncate: bool,
    ) -> tuple[Message, list[int], Meta]:
        text = self._guard.text(payload.text, truncate, context.reporter)
        extras = self._schema.send(scope, payload.extra, span=len(text), media=False)
        message = await bot.send_message(
            **context.targets,
            text=text,
            reply_markup=context.markup,
            link_preview_options=context.preview,
            **self._screen.filter(bot.send_message, extras.get("text", {})),
        )
        context.reporter.success(message.message_id, 0)
        meta = util.extract(message, payload, scope)
        return message, [], meta


__all__ = ["AlbumSender", "SingleMediaSender", "TextSender"]

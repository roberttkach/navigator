from __future__ import annotations

import logging
from aiogram import Bot
from aiogram.types import Message
from navigator.core.error import CaptionOverflow, EmptyPayload, InlineUnsupported, TextOverflow
from navigator.core.port.extraschema import ExtraSchema
from navigator.core.port.limits import Limits
from navigator.core.port.markup import MarkupCodec
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.port.preview import LinkPreviewCodec
from navigator.core.service.rendering.helpers import classify
from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.typing.result import Cluster, GroupMeta, Meta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope
from dataclasses import dataclass
from typing import Dict

from . import util
from ..media import assemble
from ..serializer import caption as captionkit
from ..serializer import text as textkit
from ..serializer.screen import SignatureScreen


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
    context_factory = SendContextFactory(codec=codec, preview=preview)
    dispatcher = SendDispatcher(
        bot,
        schema=schema,
        screen=screen,
        policy=policy,
        limits=limits,
        telemetry=telemetry,
    )
    context = context_factory.build(scope=scope, payload=payload, channel=channel)
    return await dispatcher.dispatch(
        payload,
        scope=scope,
        context=context,
        truncate=truncate,
    )


def _ensure_inline_supported(scope: Scope) -> None:
    if scope.inline:
        raise InlineUnsupported("inline_send_not_supported")


def _preview_options(preview: LinkPreviewCodec | None, payload: Payload) -> object | None:
    if preview is None or payload.preview is None:
        return None
    return preview.encode(payload.preview)


@dataclass(frozen=True)
class SendContext:
    """Bundle prepared data required to send a payload."""

    markup: object | None
    preview: object | None
    targets: Dict[str, object]
    reporter: "SendTelemetry"

    @classmethod
    def create(
        cls,
        *,
        codec: MarkupCodec,
        scope: Scope,
        payload: Payload,
        preview: LinkPreviewCodec | None,
        channel: TelemetryChannel,
    ) -> "SendContext":
        _ensure_inline_supported(scope)
        markup = textkit.decode(codec, payload.reply)
        preview_options = _preview_options(preview, payload)
        targets = util.targets(scope)
        reporter = SendTelemetry(channel, scope, payload)
        return cls(
            markup=markup,
            preview=preview_options,
            targets=targets,
            reporter=reporter,
        )


class SendTelemetry:
    def __init__(self, channel: TelemetryChannel, scope: Scope, payload: Payload) -> None:
        self._channel = channel
        self._scope = scope
        self._payload = payload

    def truncated(self, stage: str) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.TOO_LONG_TRUNCATED,
            scope=profile(self._scope),
            stage=stage,
        )

    def success(self, message_id: int, extra_len: int) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.GATEWAY_SEND_OK,
            scope=profile(self._scope),
            payload=classify(self._payload),
            message={"id": message_id, "extra_len": extra_len},
        )


class SendContextFactory:
    """Construct :class:`SendContext` instances from raw payload data."""

    def __init__(self, codec: MarkupCodec, preview: LinkPreviewCodec | None) -> None:
        self._codec = codec
        self._preview = preview

    def build(
        self,
        scope: Scope,
        payload: Payload,
        channel: TelemetryChannel,
    ) -> SendContext:
        return SendContext.create(
            codec=self._codec,
            scope=scope,
            payload=payload,
            preview=self._preview,
            channel=channel,
        )


class SendDispatcher:
    """Execute Telegram send operations using prepared context."""

    def __init__(
        self,
        bot: Bot,
        *,
        schema: ExtraSchema,
        screen: SignatureScreen,
        policy: MediaPathPolicy,
        limits: Limits,
        telemetry: Telemetry,
    ) -> None:
        self._bot = bot
        self._schema = schema
        self._screen = screen
        self._policy = policy
        self._limits = limits
        self._telemetry = telemetry

    async def dispatch(
        self,
        payload: Payload,
        *,
        scope: Scope,
        context: SendContext,
        truncate: bool,
    ) -> tuple[Message, list[int], Meta]:
        if payload.group:
            return await self._send_group(payload, scope=scope, context=context)
        if payload.media:
            return await self._send_media(
                payload,
                scope=scope,
                context=context,
                truncate=truncate,
            )
        return await self._send_text(
            payload,
            scope=scope,
            context=context,
            truncate=truncate,
        )

    async def _send_group(
        self,
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
            addition = self._screen.filter(self._bot.send_media_group, {"message_effect_id": effect})

        messages = await self._bot.send_media_group(
            media=bundle,
            **context.targets,
            **addition,
        )
        head = messages[0]
        context.reporter.success(head.message_id, len(messages) - 1)
        meta = GroupMeta(clusters=_group_clusters(messages, payload), inline=scope.inline)
        extras_ids = [message.message_id for message in messages[1:]]
        return head, extras_ids, meta

    async def _send_media(
        self,
        payload: Payload,
        *,
        scope: Scope,
        context: SendContext,
        truncate: bool,
    ) -> tuple[Message, list[int], Meta]:
        caption = captionkit.caption(payload)
        caption = _enforce_caption_limit(caption, self._limits, truncate, context.reporter)
        extras = self._schema.send(scope, payload.extra, span=len(caption or ""), media=True)
        sender = getattr(self._bot, f"send_{payload.media.type.value}")
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

    async def _send_text(
        self,
        payload: Payload,
        *,
        scope: Scope,
        context: SendContext,
        truncate: bool,
    ) -> tuple[Message, list[int], Meta]:
        text = _normalise_text(payload.text, self._limits, truncate, context.reporter)
        extras = self._schema.send(scope, payload.extra, span=len(text), media=False)
        message = await self._bot.send_message(
            **context.targets,
            text=text,
            reply_markup=context.markup,
            link_preview_options=context.preview,
            **self._screen.filter(self._bot.send_message, extras.get("text", {})),
        )
        context.reporter.success(message.message_id, 0)
        meta = util.extract(message, payload, scope)
        return message, [], meta

def _enforce_caption_limit(
    caption: str | None,
    limits: Limits,
    truncate: bool,
    reporter: SendTelemetry,
) -> str | None:
    if caption is None or len(caption) <= limits.captionlimit():
        return caption
    if truncate:
        reporter.truncated("send.caption")
        return caption[: limits.captionlimit()]
    raise CaptionOverflow()


def _normalise_text(
        text: str | None,
        limits: Limits,
        truncate: bool,
        reporter: SendTelemetry,
) -> str:
    value = text or ""
    if not value.strip():
        raise EmptyPayload()
    if len(value) <= limits.textlimit():
        return value
    if not truncate:
        raise TextOverflow()
    reporter.truncated("send.text")
    return value[: limits.textlimit()]


def _group_clusters(messages: list[Message], payload: Payload) -> list[Cluster]:
    clusters: list[Cluster] = []
    for index, message in enumerate(messages):
        member = payload.group[index] if payload.group and index < len(payload.group) else None
        medium, filetoken = _group_member_tokens(message, member)
        clusters.append(
            Cluster(
                medium=medium,
                file=filetoken,
                caption=message.caption if index == 0 else "",
            )
        )
    return clusters


def _group_member_tokens(message: Message, member) -> tuple[str | None, str | None]:
    medium = None
    filetoken = None
    if message.photo:
        medium = "photo"
        filetoken = message.photo[-1].file_id
    elif message.video:
        medium = "video"
        filetoken = message.video.file_id
    elif message.animation:
        medium = "animation"
        filetoken = message.animation.file_id
    elif message.document:
        medium = "document"
        filetoken = message.document.file_id
    elif message.audio:
        medium = "audio"
        filetoken = message.audio.file_id
    elif message.voice:
        medium = "voice"
        filetoken = message.voice.file_id
    elif message.video_note:
        medium = "video_note"
        filetoken = message.video_note.file_id

    if medium is None and member is not None:
        medium = getattr(getattr(member, "type", None), "value", None)
    if filetoken is None and member is not None:
        path = getattr(member, "path", None)
        if isinstance(path, str):
            filetoken = path
    return medium, filetoken


__all__ = ["SendContextFactory", "SendDispatcher", "send"]

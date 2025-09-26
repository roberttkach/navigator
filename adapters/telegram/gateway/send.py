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
    context = _SendContext.create(
        codec=codec,
        scope=scope,
        payload=payload,
        preview=preview,
        channel=channel,
    )

    return await _dispatch(
        bot,
        payload,
        context=context,
        schema=schema,
        screen=screen,
        policy=policy,
        limits=limits,
        truncate=truncate,
        telemetry=telemetry,
        scope=scope,
    )


def _ensure_inline_supported(scope: Scope) -> None:
    if scope.inline:
        raise InlineUnsupported("inline_send_not_supported")


def _preview_options(preview: LinkPreviewCodec | None, payload: Payload) -> object | None:
    if preview is None or payload.preview is None:
        return None
    return preview.encode(payload.preview)


@dataclass(frozen=True)
class _SendContext:
    """Bundle prepared data required to send a payload."""

    markup: object | None
    preview: object | None
    targets: Dict[str, object]
    reporter: "_SendTelemetry"

    @classmethod
    def create(
        cls,
        *,
        codec: MarkupCodec,
        scope: Scope,
        payload: Payload,
        preview: LinkPreviewCodec | None,
        channel: TelemetryChannel,
    ) -> "_SendContext":
        _ensure_inline_supported(scope)
        markup = textkit.decode(codec, payload.reply)
        preview_options = _preview_options(preview, payload)
        targets = util.targets(scope)
        reporter = _SendTelemetry(channel, scope, payload)
        return cls(
            markup=markup,
            preview=preview_options,
            targets=targets,
            reporter=reporter,
        )


class _SendTelemetry:
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


async def _send_group(
        bot: Bot,
        payload: Payload,
        *,
        context: _SendContext,
        schema: ExtraSchema,
        screen: SignatureScreen,
        policy: MediaPathPolicy,
        limits: Limits,
        telemetry: Telemetry,
        scope: Scope,
) -> tuple[Message, list[int], GroupMeta]:
    caption = captionkit.caption(payload)
    extras = schema.send(scope, payload.extra, span=len(caption or ""), media=True)
    bundle = assemble(
        payload.group,
        captionmeta=extras.get("caption", {}),
        mediameta=extras.get("media", {}),
        policy=policy,
        screen=screen,
        limits=limits,
        native=True,
        telemetry=telemetry,
    )
    effect = extras.get("effect")
    addition: Dict[str, object] = {}
    if effect is not None:
        addition = screen.filter(bot.send_media_group, {"message_effect_id": effect})

    messages = await bot.send_media_group(
        media=bundle,
        **context.targets,
        **addition,
    )
    head = messages[0]
    context.reporter.success(head.message_id, len(messages) - 1)
    meta = GroupMeta(clusters=_group_clusters(messages, payload), inline=scope.inline)
    extras_ids = [message.message_id for message in messages[1:]]
    return head, extras_ids, meta


async def _dispatch(
        bot: Bot,
        payload: Payload,
        *,
        context: _SendContext,
        schema: ExtraSchema,
        screen: SignatureScreen,
        policy: MediaPathPolicy,
        limits: Limits,
        truncate: bool,
        telemetry: Telemetry,
        scope: Scope,
) -> tuple[Message, list[int], Meta]:
    if payload.group:
        return await _send_group(
            bot,
            payload,
            context=context,
            schema=schema,
            screen=screen,
            policy=policy,
            limits=limits,
            telemetry=telemetry,
            scope=scope,
        )

    if payload.media:
        return await _send_media(
            bot,
            payload,
            context=context,
            schema=schema,
            screen=screen,
            policy=policy,
            limits=limits,
            truncate=truncate,
            scope=scope,
        )

    return await _send_text(
        bot,
        payload,
        context=context,
        schema=schema,
        screen=screen,
        limits=limits,
        truncate=truncate,
        scope=scope,
    )


async def _send_media(
        bot: Bot,
        payload: Payload,
        *,
        context: _SendContext,
        schema: ExtraSchema,
        screen: SignatureScreen,
        policy: MediaPathPolicy,
        limits: Limits,
        truncate: bool,
        scope: Scope,
) -> tuple[Message, list[int], Meta]:
    caption = captionkit.caption(payload)
    caption = _enforce_caption_limit(caption, limits, truncate, context.reporter)
    extras = schema.send(scope, payload.extra, span=len(caption or ""), media=True)
    sender = getattr(bot, f"send_{payload.media.type.value}")
    arguments = {
        **context.targets,
        payload.media.type.value: policy.adapt(payload.media.path, native=True),
        "reply_markup": context.markup,
    }
    if caption is not None:
        arguments["caption"] = caption
    arguments.update(screen.filter(sender, extras.get("caption", {})))
    arguments.update(screen.filter(sender, extras.get("media", {})))
    message = await sender(**arguments)
    context.reporter.success(message.message_id, 0)
    meta = util.extract(message, payload, scope)
    return message, [], meta


async def _send_text(
        bot: Bot,
        payload: Payload,
        *,
        context: _SendContext,
        schema: ExtraSchema,
        screen: SignatureScreen,
        limits: Limits,
        truncate: bool,
        scope: Scope,
) -> tuple[Message, list[int], Meta]:
    text = _normalise_text(payload.text, limits, truncate, context.reporter)
    extras = schema.send(scope, payload.extra, span=len(text), media=False)
    message = await bot.send_message(
        **context.targets,
        text=text,
        reply_markup=context.markup,
        link_preview_options=context.preview,
        **screen.filter(bot.send_message, extras.get("text", {})),
    )
    context.reporter.success(message.message_id, 0)
    meta = util.extract(message, payload, scope)
    return message, [], meta


def _enforce_caption_limit(
        caption: str | None,
        limits: Limits,
        truncate: bool,
        reporter: _SendTelemetry,
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
        reporter: _SendTelemetry,
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


__all__ = ["send"]

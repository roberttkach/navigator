from __future__ import annotations

import logging
from typing import Dict

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
from navigator.core.telemetry import LogCode, telemetry
from navigator.core.typing.result import Cluster, GroupMeta, Meta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ..media import assemble
from ..serializer import caption as caption_tools
from ..serializer import text as text_tools
from ..serializer.screen import SignatureScreen
from . import util

channel = telemetry.channel(__name__)


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
) -> tuple[Message, list[int], Meta]:
    if scope.inline:
        raise InlineUnsupported("inline_send_not_supported")

    reply_markup = text_tools.decode(codec, payload.reply)
    options = None
    if preview is not None and payload.preview is not None:
        options = preview.encode(payload.preview)
    targets = util.targets(scope)

    if payload.group:
        caption_text = caption_tools.caption(payload)
        extras = schema.for_send(scope, payload.extra, caption_len=len(caption_text or ""), media=True)
        effect = extras.get("effect")
        bundle = assemble(
            payload.group,
            caption_extra=extras.get("caption", {}),
            media_extra=extras.get("media", {}),
            policy=policy,
            screen=screen,
            limits=limits,
            native=True,
        )
        addition: Dict[str, object] = {}
        if effect is not None:
            addition = screen.filter(bot.send_media_group, {"message_effect_id": effect})
        messages = await bot.send_media_group(
            media=bundle,
            **targets,
            **addition,
        )
        head = messages[0]
        clusters: list[Cluster] = []
        for index, message in enumerate(messages):
            payload_item = None
            if payload.group and index < len(payload.group):
                payload_item = payload.group[index]
            medium = None
            file_id = None
            if message.photo:
                medium = "photo"
                file_id = message.photo[-1].file_id
            elif message.video:
                medium = "video"
                file_id = message.video.file_id
            elif message.animation:
                medium = "animation"
                file_id = message.animation.file_id
            elif message.document:
                medium = "document"
                file_id = message.document.file_id
            elif message.audio:
                medium = "audio"
                file_id = message.audio.file_id
            elif message.voice:
                medium = "voice"
                file_id = message.voice.file_id
            elif message.video_note:
                medium = "video_note"
                file_id = message.video_note.file_id
            if medium is None and payload_item is not None:
                medium = getattr(getattr(payload_item, "type", None), "value", None)
            if file_id is None and payload_item is not None:
                path = getattr(payload_item, "path", None)
                if isinstance(path, str):
                    file_id = path
            clusters.append(
                Cluster(
                    medium=medium,
                    file=file_id,
                    caption=message.caption if index == 0 else "",
                )
            )
        meta = GroupMeta(clusters=clusters, inline=scope.inline)
        channel.emit(
            logging.INFO,
            LogCode.GATEWAY_SEND_OK,
            scope=profile(scope),
            payload=classify(payload),
            message={"id": head.message_id, "extra_len": len(messages) - 1},
        )
        extras = [message.message_id for message in messages[1:]]
        return head, extras, meta

    if payload.media:
        caption_text = caption_tools.caption(payload)
        if caption_text is not None and len(caption_text) > limits.caption_max():
            if truncate:
                caption_text = caption_text[: limits.caption_max()]
                channel.emit(
                    logging.INFO,
                    LogCode.TOO_LONG_TRUNCATED,
                    scope=profile(scope),
                    stage="send.caption",
                )
            else:
                raise CaptionOverflow()
        extras = schema.for_send(scope, payload.extra, caption_len=len(caption_text or ""), media=True)
        sender = getattr(bot, f"send_{payload.media.type.value}")
        arguments = {
            **targets,
            payload.media.type.value: policy.adapt(payload.media.path, native=True),
            "reply_markup": reply_markup,
        }
        if caption_text is not None:
            arguments["caption"] = caption_text
        arguments.update(screen.filter(sender, extras.get("caption", {})))
        arguments.update(screen.filter(sender, extras.get("media", {})))
        message = await sender(**arguments)
        channel.emit(
            logging.INFO,
            LogCode.GATEWAY_SEND_OK,
            scope=profile(scope),
            payload=classify(payload),
            message={"id": message.message_id, "extra_len": 0},
        )
        meta = util.extract(message, payload, scope)
        return message, [], meta

    text = payload.text or ""
    if not text.strip():
        raise EmptyPayload()
    if len(text) > limits.text_max():
        if truncate:
            text = text[: limits.text_max()]
            channel.emit(
                logging.INFO,
                LogCode.TOO_LONG_TRUNCATED,
                scope=profile(scope),
                stage="send.text",
            )
        else:
            raise TextOverflow()
    extras = schema.for_send(scope, payload.extra, caption_len=len(text), media=False)
    message = await bot.send_message(
        **targets,
        text=text,
        reply_markup=reply_markup,
        link_preview_options=options,
        **screen.filter(bot.send_message, extras.get("text", {})),
    )
    channel.emit(
        logging.INFO,
        LogCode.GATEWAY_SEND_OK,
        scope=profile(scope),
        payload=classify(payload),
        message={"id": message.message_id, "extra_len": 0},
    )
    meta = util.extract(message, payload, scope)
    return message, [], meta


__all__ = ["send"]

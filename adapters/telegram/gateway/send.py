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
    if scope.inline:
        raise InlineUnsupported("inline_send_not_supported")

    markup = textkit.decode(codec, payload.reply)
    options = None
    if preview is not None and payload.preview is not None:
        options = preview.encode(payload.preview)
    targets = util.targets(scope)

    if payload.group:
        caption = captionkit.caption(payload)
        extras = schema.send(scope, payload.extra, span=len(caption or ""), media=True)
        effect = extras.get("effect")
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
            member = None
            if payload.group and index < len(payload.group):
                member = payload.group[index]
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
            clusters.append(
                Cluster(
                    medium=medium,
                    file=filetoken,
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
        caption = captionkit.caption(payload)
        if caption is not None and len(caption) > limits.captionlimit():
            if truncate:
                caption = caption[: limits.captionlimit()]
                channel.emit(
                    logging.INFO,
                    LogCode.TOO_LONG_TRUNCATED,
                    scope=profile(scope),
                    stage="send.caption",
                )
            else:
                raise CaptionOverflow()
        extras = schema.send(scope, payload.extra, span=len(caption or ""), media=True)
        sender = getattr(bot, f"send_{payload.media.type.value}")
        arguments = {
            **targets,
            payload.media.type.value: policy.adapt(payload.media.path, native=True),
            "reply_markup": markup,
        }
        if caption is not None:
            arguments["caption"] = caption
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
    if len(text) > limits.textlimit():
        if truncate:
            text = text[: limits.textlimit()]
            channel.emit(
                logging.INFO,
                LogCode.TOO_LONG_TRUNCATED,
                scope=profile(scope),
                stage="send.text",
            )
        else:
            raise TextOverflow()
    extras = schema.send(scope, payload.extra, span=len(text), media=False)
    message = await bot.send_message(
        **targets,
        text=text,
        reply_markup=markup,
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

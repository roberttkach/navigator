from __future__ import annotations

import logging
from aiogram import Bot
from navigator.core.error import CaptionOverflow, TextOverflow
from navigator.core.port.extraschema import ExtraSchema
from navigator.core.port.limits import Limits
from navigator.core.port.markup import MarkupCodec
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.port.preview import LinkPreviewCodec
from navigator.core.service.rendering.helpers import classify
from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, TelemetryChannel
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from . import util
from ..media import compose
from ..serializer import caption as captionkit
from ..serializer import text as textkit
from ..serializer.screen import SignatureScreen


async def rewrite(
        bot: Bot,
        *,
        codec: MarkupCodec,
        schema: ExtraSchema,
        screen: SignatureScreen,
        limits: Limits,
        preview: LinkPreviewCodec | None,
        scope: Scope,
        identifier: int,
        payload: Payload,
        truncate: bool,
        channel: TelemetryChannel,
):
    text = payload.text or ""
    if len(text) > limits.textlimit():
        if truncate:
            text = text[: limits.textlimit()]
            channel.emit(
                logging.INFO,
                LogCode.TOO_LONG_TRUNCATED,
                scope=profile(scope),
                stage="edit.text",
            )
        else:
            raise TextOverflow()
    extras = schema.edit(scope, payload.extra, span=len(text), media=False)
    markup = textkit.decode(codec, payload.reply)
    options = None
    if preview is not None and payload.preview is not None:
        options = preview.encode(payload.preview)
    message = await bot.edit_message_text(
        **util.targets(scope, identifier),
        text=text,
        reply_markup=markup,
        link_preview_options=options,
        **screen.filter(bot.edit_message_text, extras.get("text", {})),
    )
    channel.emit(
        logging.INFO,
        LogCode.GATEWAY_EDIT_OK,
        scope=profile(scope),
        payload=classify(payload),
        message={"id": message.message_id if hasattr(message, "message_id") else identifier, "extra_len": 0},
    )
    return message


async def recast(
        bot: Bot,
        *,
        codec: MarkupCodec,
        schema: ExtraSchema,
        screen: SignatureScreen,
        policy: MediaPathPolicy,
        limits: Limits,
        scope: Scope,
        identifier: int,
        payload: Payload,
        truncate: bool,
        channel: TelemetryChannel,
):
    caption = captionkit.caption(payload)
    if caption is not None and len(caption) > limits.captionlimit():
        if truncate:
            caption = caption[: limits.captionlimit()]
            channel.emit(
                logging.INFO,
                LogCode.TOO_LONG_TRUNCATED,
                scope=profile(scope),
                stage="edit.caption",
            )
        else:
            raise CaptionOverflow()
    extras = schema.edit(scope, payload.extra, span=len(caption or ""), media=True)
    media = compose(
        payload.media,
        caption=caption,
        captionmeta=extras.get("caption", {}),
        mediameta=extras.get("media", {}),
        policy=policy,
        screen=screen,
        limits=limits,
        native=not scope.inline,
    )
    markup = textkit.decode(codec, payload.reply)
    message = await bot.edit_message_media(
        media=media,
        reply_markup=markup,
        **util.targets(scope, identifier),
    )
    channel.emit(
        logging.INFO,
        LogCode.GATEWAY_EDIT_OK,
        scope=profile(scope),
        payload=classify(payload),
        message={"id": message.message_id if hasattr(message, "message_id") else identifier, "extra_len": 0},
    )
    return message


async def retitle(
        bot: Bot,
        *,
        codec: MarkupCodec,
        schema: ExtraSchema,
        screen: SignatureScreen,
        limits: Limits,
        scope: Scope,
        identifier: int,
        payload: Payload,
        truncate: bool,
        channel: TelemetryChannel,
):
    caption = captionkit.restate(payload)
    if caption is not None and len(caption) > limits.captionlimit():
        if truncate:
            caption = caption[: limits.captionlimit()]
            channel.emit(
                logging.INFO,
                LogCode.TOO_LONG_TRUNCATED,
                scope=profile(scope),
                stage="edit.caption",
            )
        else:
            raise CaptionOverflow()
    extras = schema.edit(scope, payload.extra, span=len(caption or ""), media=True)
    markup = textkit.decode(codec, payload.reply)
    message = await bot.edit_message_caption(
        **util.targets(scope, identifier),
        caption=caption,
        reply_markup=markup,
        **screen.filter(bot.edit_message_caption, extras.get("caption", {})),
    )
    channel.emit(
        logging.INFO,
        LogCode.GATEWAY_EDIT_OK,
        scope=profile(scope),
        payload=classify(payload),
        message={"id": message.message_id if hasattr(message, "message_id") else identifier, "extra_len": 0},
    )
    return message


async def remap(
        bot: Bot,
        *,
        codec: MarkupCodec,
        scope: Scope,
        identifier: int,
        payload: Payload,
        channel: TelemetryChannel,
):
    markup = textkit.decode(codec, payload.reply)
    message = await bot.edit_message_reply_markup(
        **util.targets(scope, identifier),
        reply_markup=markup,
    )
    channel.emit(
        logging.INFO,
        LogCode.GATEWAY_EDIT_OK,
        scope=profile(scope),
        payload=classify(payload),
        message={"id": message.message_id if hasattr(message, "message_id") else identifier, "extra_len": 0},
    )
    return message


__all__ = ["rewrite", "recast", "retitle", "remap"]

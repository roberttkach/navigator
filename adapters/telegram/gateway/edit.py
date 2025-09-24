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

from ..media import compose
from ..serializer import caption as caption_tools
from ..serializer import text as text_tools
from ..serializer.screen import SignatureScreen
from . import util

async def rewrite(
    bot: Bot,
    *,
    codec: MarkupCodec,
    schema: ExtraSchema,
    screen: SignatureScreen,
    limits: Limits,
    preview: LinkPreviewCodec | None,
    scope: Scope,
    message_id: int,
    payload: Payload,
    truncate: bool,
    channel: TelemetryChannel,
):
    text = payload.text or ""
    if len(text) > limits.text_max():
        if truncate:
            text = text[: limits.text_max()]
            channel.emit(
                logging.INFO,
                LogCode.TOO_LONG_TRUNCATED,
                scope=profile(scope),
                stage="edit.text",
            )
        else:
            raise TextOverflow()
    extras = schema.for_edit(scope, payload.extra, caption_len=len(text), media=False)
    markup = text_tools.decode(codec, payload.reply)
    options = None
    if preview is not None and payload.preview is not None:
        options = preview.encode(payload.preview)
    message = await bot.edit_message_text(
        **util.targets(scope, message_id),
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
        message={"id": message.message_id if hasattr(message, "message_id") else message_id, "extra_len": 0},
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
    message_id: int,
    payload: Payload,
    truncate: bool,
    channel: TelemetryChannel,
):
    caption_text = caption_tools.caption(payload)
    if caption_text is not None and len(caption_text) > limits.caption_max():
        if truncate:
            caption_text = caption_text[: limits.caption_max()]
            channel.emit(
                logging.INFO,
                LogCode.TOO_LONG_TRUNCATED,
                scope=profile(scope),
                stage="edit.caption",
            )
        else:
            raise CaptionOverflow()
    extras = schema.for_edit(scope, payload.extra, caption_len=len(caption_text or ""), media=True)
    media = compose(
        payload.media,
        caption=caption_text,
        caption_extra=extras.get("caption", {}),
        media_extra=extras.get("media", {}),
        policy=policy,
        screen=screen,
        limits=limits,
        native=not scope.inline,
    )
    markup = text_tools.decode(codec, payload.reply)
    message = await bot.edit_message_media(
        media=media,
        reply_markup=markup,
        **util.targets(scope, message_id),
    )
    channel.emit(
        logging.INFO,
        LogCode.GATEWAY_EDIT_OK,
        scope=profile(scope),
        payload=classify(payload),
        message={"id": message.message_id if hasattr(message, "message_id") else message_id, "extra_len": 0},
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
    message_id: int,
    payload: Payload,
    truncate: bool,
    channel: TelemetryChannel,
):
    caption_text = caption_tools.restate(payload)
    if caption_text is not None and len(caption_text) > limits.caption_max():
        if truncate:
            caption_text = caption_text[: limits.caption_max()]
            channel.emit(
                logging.INFO,
                LogCode.TOO_LONG_TRUNCATED,
                scope=profile(scope),
                stage="edit.caption",
            )
        else:
            raise CaptionOverflow()
    extras = schema.for_edit(scope, payload.extra, caption_len=len(caption_text or ""), media=True)
    markup = text_tools.decode(codec, payload.reply)
    message = await bot.edit_message_caption(
        **util.targets(scope, message_id),
        caption=caption_text,
        reply_markup=markup,
        **screen.filter(bot.edit_message_caption, extras.get("caption", {})),
    )
    channel.emit(
        logging.INFO,
        LogCode.GATEWAY_EDIT_OK,
        scope=profile(scope),
        payload=classify(payload),
        message={"id": message.message_id if hasattr(message, "message_id") else message_id, "extra_len": 0},
    )
    return message


async def remap(
    bot: Bot,
    *,
    codec: MarkupCodec,
    scope: Scope,
    message_id: int,
    payload: Payload,
    channel: TelemetryChannel,
):
    markup = text_tools.decode(codec, payload.reply)
    message = await bot.edit_message_reply_markup(
        **util.targets(scope, message_id),
        reply_markup=markup,
    )
    channel.emit(
        logging.INFO,
        LogCode.GATEWAY_EDIT_OK,
        scope=profile(scope),
        payload=classify(payload),
        message={"id": message.message_id if hasattr(message, "message_id") else message_id, "extra_len": 0},
    )
    return message


__all__ = ["rewrite", "recast", "retitle", "remap"]

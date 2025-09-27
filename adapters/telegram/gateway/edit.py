from __future__ import annotations

import logging
from aiogram import Bot
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

from .targeting import resolve_targets
from ..serializer.screen import SignatureScreen
from .planner import (
    emit_telemetry,
    prepare_caption_edit,
    prepare_media_edit,
    prepare_markup_edit,
    prepare_text_edit,
)


def _log_success(
    channel: TelemetryChannel,
    scope: Scope,
    payload: Payload,
    identifier: int,
    message: object,
) -> None:
    channel.emit(
        logging.INFO,
        LogCode.GATEWAY_EDIT_OK,
        scope=profile(scope),
        payload=classify(payload),
        message={
            "id": getattr(message, "message_id", identifier),
            "extra_len": 0,
        },
    )


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
    plan = prepare_text_edit(
        payload,
        codec=codec,
        schema=schema,
        limits=limits,
        preview=preview,
        scope=scope,
        truncate=truncate,
    )
    emit_telemetry(channel, plan.telemetry)
    message = await bot.edit_message_text(
        **resolve_targets(scope, identifier),
        text=plan.text,
        reply_markup=plan.markup,
        link_preview_options=plan.preview_options,
        **screen.filter(bot.edit_message_text, plan.extras.get("text", {})),
    )
    _log_success(channel, scope, payload, identifier, message)
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
    plan = prepare_media_edit(
        payload,
        codec=codec,
        schema=schema,
        screen=screen,
        policy=policy,
        limits=limits,
        scope=scope,
        truncate=truncate,
    )
    emit_telemetry(channel, plan.telemetry)
    message = await bot.edit_message_media(
        media=plan.media,
        reply_markup=plan.markup,
        **resolve_targets(scope, identifier),
    )
    _log_success(channel, scope, payload, identifier, message)
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
    plan = prepare_caption_edit(
        payload,
        codec=codec,
        schema=schema,
        limits=limits,
        scope=scope,
        truncate=truncate,
    )
    emit_telemetry(channel, plan.telemetry)
    message = await bot.edit_message_caption(
        **resolve_targets(scope, identifier),
        caption=plan.caption,
        reply_markup=plan.markup,
        **screen.filter(bot.edit_message_caption, plan.extras.get("caption", {})),
    )
    _log_success(channel, scope, payload, identifier, message)
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
    plan = prepare_markup_edit(payload, codec=codec)
    message = await bot.edit_message_reply_markup(
        **resolve_targets(scope, identifier),
        reply_markup=plan.markup,
    )
    _log_success(channel, scope, payload, identifier, message)
    return message


__all__ = ["rewrite", "recast", "retitle", "remap"]

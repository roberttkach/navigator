"""Prepare Telegram edit requests decoupled from bot operations."""
from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Iterable, Mapping, Sequence

from navigator.core.error import CaptionOverflow, TextOverflow
from navigator.core.port.extraschema import ExtraSchema
from navigator.core.port.limits import Limits
from navigator.core.port.markup import MarkupCodec
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.port.preview import LinkPreviewCodec
from navigator.core.telemetry import LogCode, TelemetryChannel
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope
from . import util
from ..media import compose
from ..serializer import caption as captionkit
from ..serializer import text as textkit
from ..serializer.screen import SignatureScreen


@dataclass(frozen=True)
class TelemetryEvent:
    """Structured telemetry emission request."""

    level: int
    code: LogCode
    fields: Mapping[str, object]


@dataclass(frozen=True)
class TextEditPlan:
    """Prepared data for ``edit_message_text`` operations."""

    text: str
    markup: object
    extras: Mapping[str, object]
    preview_options: object | None
    telemetry: Sequence[TelemetryEvent]


@dataclass(frozen=True)
class MediaEditPlan:
    """Prepared data for ``edit_message_media`` operations."""

    media: object
    markup: object
    extras: Mapping[str, object]
    telemetry: Sequence[TelemetryEvent]


@dataclass(frozen=True)
class CaptionEditPlan:
    """Prepared data for ``edit_message_caption`` operations."""

    caption: str | None
    markup: object
    extras: Mapping[str, object]
    telemetry: Sequence[TelemetryEvent]


@dataclass(frozen=True)
class MarkupEditPlan:
    """Prepared data for ``edit_message_reply_markup`` operations."""

    markup: object


def _truncate_event(scope: Scope, *, stage: str) -> TelemetryEvent:
    return TelemetryEvent(
        logging.INFO,
        LogCode.TOO_LONG_TRUNCATED,
        {"scope": util.profile(scope), "stage": stage},
    )


def prepare_text_edit(
    payload: Payload,
    *,
    codec: MarkupCodec,
    schema: ExtraSchema,
    limits: Limits,
    preview: LinkPreviewCodec | None,
    scope: Scope,
    truncate: bool,
) -> TextEditPlan:
    """Return text edit inputs applying policy checks."""

    text = payload.text or ""
    events: list[TelemetryEvent] = []
    limit = limits.textlimit()
    if len(text) > limit:
        if truncate:
            text = text[:limit]
            events.append(_truncate_event(scope, stage="edit.text"))
        else:
            raise TextOverflow()

    extras = schema.edit(scope, payload.extra, span=len(text), media=False)
    markup = textkit.decode(codec, payload.reply)
    options = None
    if preview is not None and payload.preview is not None:
        options = preview.encode(payload.preview)

    return TextEditPlan(
        text=text,
        markup=markup,
        extras=extras,
        preview_options=options,
        telemetry=tuple(events),
    )


def prepare_media_edit(
    payload: Payload,
    *,
    codec: MarkupCodec,
    schema: ExtraSchema,
    screen: SignatureScreen,
    policy: MediaPathPolicy,
    limits: Limits,
    scope: Scope,
    truncate: bool,
) -> MediaEditPlan:
    """Return media edit inputs applying caption constraints."""

    caption = captionkit.caption(payload)
    events: list[TelemetryEvent] = []
    limit = limits.captionlimit()
    if caption is not None and len(caption) > limit:
        if truncate:
            caption = caption[:limit]
            events.append(_truncate_event(scope, stage="edit.caption"))
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

    return MediaEditPlan(
        media=media,
        markup=markup,
        extras=extras,
        telemetry=tuple(events),
    )


def prepare_caption_edit(
    payload: Payload,
    *,
    codec: MarkupCodec,
    schema: ExtraSchema,
    limits: Limits,
    scope: Scope,
    truncate: bool,
) -> CaptionEditPlan:
    """Return caption edit inputs with guardrails applied."""

    caption = captionkit.restate(payload)
    events: list[TelemetryEvent] = []
    limit = limits.captionlimit()
    if caption is not None and len(caption) > limit:
        if truncate:
            caption = caption[:limit]
            events.append(_truncate_event(scope, stage="edit.caption"))
        else:
            raise CaptionOverflow()

    extras = schema.edit(scope, payload.extra, span=len(caption or ""), media=True)
    markup = textkit.decode(codec, payload.reply)

    return CaptionEditPlan(
        caption=caption,
        markup=markup,
        extras=extras,
        telemetry=tuple(events),
    )


def prepare_markup_edit(
    payload: Payload,
    *,
    codec: MarkupCodec,
) -> MarkupEditPlan:
    """Prepare reply markup edits."""

    markup = textkit.decode(codec, payload.reply)
    return MarkupEditPlan(markup=markup)


def emit_telemetry(
    channel: TelemetryChannel, events: Iterable[TelemetryEvent]
) -> None:
    """Forward prepared telemetry events to ``channel``."""

    for event in events:
        channel.emit(event.level, event.code, **event.fields)


__all__ = [
    "CaptionEditPlan",
    "MediaEditPlan",
    "MarkupEditPlan",
    "TelemetryEvent",
    "TextEditPlan",
    "emit_telemetry",
    "prepare_caption_edit",
    "prepare_media_edit",
    "prepare_markup_edit",
    "prepare_text_edit",
]

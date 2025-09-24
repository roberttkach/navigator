from __future__ import annotations

from dataclasses import replace
from typing import Any, Dict, Optional

from aiogram.types import Message

from navigator.core.port.message import Result
from navigator.core.typing.result import MediaMeta, Meta, TextMeta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope


def targets(scope: Scope, message: Optional[int] = None, *, topical: bool = True) -> Dict[str, Any]:
    if scope.inline:
        data: Dict[str, Any] = {"inline_message_id": scope.inline}
    else:
        data = {"chat_id": scope.chat}
        if message is not None:
            data["message_id"] = message
    if scope.business:
        data["business_connection_id"] = scope.business
    if topical and scope.topic is not None:
        data["direct_messages_topic_id"] = scope.topic
    return data


def _digest(message: Message) -> Meta:
    if getattr(message, "media_group_id", None):
        raise ValueError("grouped messages must be handled separately")
    if message.text is not None and not any(
        [message.photo, message.document, message.video, message.audio, message.animation]
    ):
        return TextMeta(text=message.text)
    if message.photo:
        return MediaMeta(medium="photo", file=message.photo[-1].file_id, caption=message.caption)
    if message.video:
        return MediaMeta(medium="video", file=message.video.file_id, caption=message.caption)
    if message.animation:
        return MediaMeta(medium="animation", file=message.animation.file_id, caption=message.caption)
    if message.document:
        return MediaMeta(medium="document", file=message.document.file_id, caption=message.caption)
    if message.audio:
        return MediaMeta(medium="audio", file=message.audio.file_id, caption=message.caption)
    if message.voice:
        return MediaMeta(medium="voice", file=message.voice.file_id, caption=message.caption)
    if message.video_note:
        return MediaMeta(medium="video_note", file=message.video_note.file_id, caption=None)
    return TextMeta(text=message.text)


def extract(outcome: Any, payload: Payload, scope: Scope) -> Meta:
    token = getattr(scope, "inline", None)
    if isinstance(outcome, Message):
        meta = _digest(outcome)
        return replace(meta, inline=token)
    if getattr(payload, "group", None):
        raise AssertionError("grouped payloads handled separately")
    if getattr(payload, "media", None):
        media = getattr(payload.media.type, "value", None)
        return MediaMeta(medium=media, file=None, caption=None, inline=token)
    return TextMeta(text=getattr(payload, "text", None), inline=token)


def derive(message: Message, payload: Payload, scope: Scope) -> Result:
    meta = extract(message, payload, scope)
    identifier = message.message_id
    return Result(id=identifier, extra=[], meta=meta)


__all__ = ["targets", "extract", "derive"]

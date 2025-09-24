from __future__ import annotations

from typing import Any, Dict, Optional

from aiogram.types import Message

from navigator.domain.port.message import Result
from navigator.domain.value.content import Payload
from navigator.domain.value.message import Scope


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


def _digest(message: Message) -> dict:
    if getattr(message, "media_group_id", None):
        raise ValueError("grouped messages must be handled separately")
    if message.text is not None and not any(
        [message.photo, message.document, message.video, message.audio, message.animation]
    ):
        return {"kind": "text", "text": message.text, "inline": None}
    if message.photo:
        return {
            "kind": "media",
            "medium": "photo",
            "file": message.photo[-1].file_id,
            "caption": message.caption,
            "inline": None,
        }
    if message.video:
        return {
            "kind": "media",
            "medium": "video",
            "file": message.video.file_id,
            "caption": message.caption,
            "inline": None,
        }
    if message.animation:
        return {
            "kind": "media",
            "medium": "animation",
            "file": message.animation.file_id,
            "caption": message.caption,
            "inline": None,
        }
    if message.document:
        return {
            "kind": "media",
            "medium": "document",
            "file": message.document.file_id,
            "caption": message.caption,
            "inline": None,
        }
    if message.audio:
        return {
            "kind": "media",
            "medium": "audio",
            "file": message.audio.file_id,
            "caption": message.caption,
            "inline": None,
        }
    if message.voice:
        return {
            "kind": "media",
            "medium": "voice",
            "file": message.voice.file_id,
            "caption": message.caption,
            "inline": None,
        }
    if message.video_note:
        return {
            "kind": "media",
            "medium": "video_note",
            "file": message.video_note.file_id,
            "caption": None,
            "inline": None,
        }
    return {"kind": "text", "text": message.text, "inline": None}


def extract(outcome: Any, payload: Payload, scope: Scope) -> dict:
    token = getattr(scope, "inline", None)
    if isinstance(outcome, Message):
        body = _digest(outcome)
        body["inline"] = token
        return body
    if getattr(payload, "group", None):
        raise AssertionError("grouped payloads handled separately")
    if getattr(payload, "media", None):
        media = getattr(payload.media.type, "value", None)
        return {
            "kind": "media",
            "medium": media,
            "file": None,
            "caption": None,
            "text": None,
            "clusters": None,
            "inline": token,
        }
    return {"kind": "text", "text": getattr(payload, "text", None), "inline": token}


def result_from_message(message: Message, payload: Payload, scope: Scope) -> Result:
    body = extract(message, payload, scope)
    identifier = message.message_id
    return Result(id=identifier, extra=[], **body)


__all__ = ["targets", "extract", "result_from_message"]

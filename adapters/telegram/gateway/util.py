from typing import Any, Dict, Optional

from aiogram.types import Message

from ....domain.value.message import Scope


def targets(scope: Scope, message: Optional[int] = None) -> Dict[str, Any]:
    if scope.inline:
        data: Dict[str, Any] = {"inline_message_id": scope.inline}
    else:
        data = {"chat_id": scope.chat}
        if message is not None:
            data["message_id"] = message
    if scope.business:
        data["business_connection_id"] = scope.business
    if scope.topic is not None:
        data["direct_messages_topic_id"] = scope.topic
    return data


def _digest(message: Message) -> dict:
    if getattr(message, "media_group_id", None):
        pass
    if getattr(message, "text", None) is not None and not getattr(message, "photo", None) \
            and not getattr(message, "document", None) and not getattr(message, "video", None) \
            and not getattr(message, "audio", None) and not getattr(message, "animation", None):
        return {"kind": "text", "text": message.text, "inline": None}
    if getattr(message, "photo", None):
        return {"kind": "media", "media_type": "photo", "file_id": message.photo[-1].file_id, "caption": message.caption, "inline": None}
    if getattr(message, "video", None):
        return {"kind": "media", "media_type": "video", "file_id": message.video.file_id, "caption": message.caption,
                "inline": None}
    if getattr(message, "animation", None):
        return {"kind": "media", "media_type": "animation", "file_id": message.animation.file_id, "caption": message.caption,
                "inline": None}
    if getattr(message, "document", None):
        return {"kind": "media", "media_type": "document", "file_id": message.document.file_id, "caption": message.caption,
                "inline": None}
    if getattr(message, "audio", None):
        return {"kind": "media", "media_type": "audio", "file_id": message.audio.file_id, "caption": message.caption,
                "inline": None}
    if getattr(message, "voice", None):
        return {"kind": "media", "media_type": "voice", "file_id": message.voice.file_id, "caption": message.caption,
                "inline": None}
    if getattr(message, "video_note", None):
        return {"kind": "media", "media_type": "video_note", "file_id": message.video_note.file_id, "caption": None,
                "inline": None}
    return {"kind": "text", "text": getattr(message, "text", None), "inline": None}


def extract(outcome: Any, payload: Any, scope: Scope) -> dict:
    """
    Возвращает dict: kind, media_type, file_id, caption, text, group_items, inline.
    Для inline всегда проставлять inline из scope.
    Для media_group собирать group_items в send.py и передавать сюда готовым dict.
    """
    token = getattr(scope, "inline", None)
    if hasattr(outcome, "message_id"):
        body = _digest(outcome)
        body["inline"] = token
        return body
    if getattr(payload, "group", None):
        return {"kind": "group", "group_items": None, "inline": token}
    if getattr(payload, "media", None):
        media = getattr(payload.media.type, "value", None)
        return {
            "kind": "media",
            "media_type": media,
            "file_id": None,
            "caption": None,
            "text": None,
            "group_items": None,
            "inline": token,
        }
    return {"kind": "text", "text": getattr(payload, "text", None), "inline": token}

from typing import Any, Dict, Optional

from aiogram.types import Message

from ....domain.value.message import Scope


def targets(scope: Scope, message_id: Optional[int] = None) -> Dict[str, Any]:
    if scope.inline:
        data: Dict[str, Any] = {"inline_message_id": scope.inline}
    else:
        data = {"chat_id": scope.chat}
        if message_id is not None:
            data["message_id"] = message_id
    if scope.business:
        data["business_connection_id"] = scope.business
    if scope.direct_topic_id is not None:
        data["direct_messages_topic_id"] = scope.direct_topic_id
    return data


def _msg_to_meta(msg: Message) -> dict:
    # kind / media_type / file_id / caption / text / group_items
    if getattr(msg, "media_group_id", None):
        # для одиночного Message не используется; группы собираются в send.py
        pass
    # чистый текст
    if getattr(msg, "text", None) is not None and not getattr(msg, "photo", None) \
            and not getattr(msg, "document", None) and not getattr(msg, "video", None) \
            and not getattr(msg, "audio", None) and not getattr(msg, "animation", None):
        return {"kind": "text", "text": msg.text, "inline_id": None}
    # media, порядок: photo, video, animation, document, audio, voice, video_note
    if getattr(msg, "photo", None):
        fid = msg.photo[-1].file_id
        return {"kind": "media", "media_type": "photo", "file_id": fid, "caption": msg.caption, "inline_id": None}
    if getattr(msg, "video", None):
        return {"kind": "media", "media_type": "video", "file_id": msg.video.file_id, "caption": msg.caption,
                "inline_id": None}
    if getattr(msg, "animation", None):
        return {"kind": "media", "media_type": "animation", "file_id": msg.animation.file_id, "caption": msg.caption,
                "inline_id": None}
    if getattr(msg, "document", None):
        return {"kind": "media", "media_type": "document", "file_id": msg.document.file_id, "caption": msg.caption,
                "inline_id": None}
    if getattr(msg, "audio", None):
        return {"kind": "media", "media_type": "audio", "file_id": msg.audio.file_id, "caption": msg.caption,
                "inline_id": None}
    if getattr(msg, "voice", None):
        return {"kind": "media", "media_type": "voice", "file_id": msg.voice.file_id, "caption": msg.caption,
                "inline_id": None}
    if getattr(msg, "video_note", None):
        return {"kind": "media", "media_type": "video_note", "file_id": msg.video_note.file_id, "caption": None,
                "inline_id": None}
    # fallback
    return {"kind": "text", "text": getattr(msg, "text", None), "inline_id": None}


def extract_meta(result_msg_or_bool: Any, payload: Any, scope: Scope) -> dict:
    """
    Возвращает dict: kind, media_type, file_id, caption, text, group_items, inline_id.
    Для inline всегда проставлять inline_id из scope.
    Для media_group собирать group_items в send.py и передавать сюда готовым dict.
    """
    inline_id = getattr(scope, "inline", None)
    if hasattr(result_msg_or_bool, "message_id"):
        m = _msg_to_meta(result_msg_or_bool)
        m["inline_id"] = inline_id
        return m
    # для edit_caption/edit_markup, когда Telegram возвращает bool
    # ориентируемся на payload
    if getattr(payload, "group", None):
        return {"kind": "group", "group_items": None, "inline_id": inline_id}
    if getattr(payload, "media", None):
        mt = getattr(payload.media.type, "value", None)
        return {
            "kind": "media",
            "media_type": mt,
            "file_id": None,  # при edit без смены файла Telegram не присылает новый file_id
            "caption": None,
            "text": None,
            "group_items": None,
            "inline_id": inline_id,
        }
    return {"kind": "text", "text": getattr(payload, "text", None), "inline_id": inline_id}

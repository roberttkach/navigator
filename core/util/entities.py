from __future__ import annotations

import logging
from typing import Any, Dict, List

from ..telemetry import LogCode, telemetry

channel = telemetry.channel(__name__)

_ALLOWED_ENTITY_TYPES = {
    "mention",
    "hashtag",
    "cashtag",
    "bot_command",
    "url",
    "email",
    "phone_number",
    "bold",
    "italic",
    "underline",
    "strikethrough",
    "spoiler",
    "code",
    "pre",
    "text_link",
    "text_mention",
    "custom_emoji",
    "blockquote",
    "expandable_blockquote",
}


def sanitize(entities: Any, length: int) -> List[Dict[str, Any]]:
    result: List[Dict[str, Any]] = []
    if not isinstance(entities, list):
        return result
    for entity in entities:
        if not isinstance(entity, dict):
            continue
        kind = entity.get("type")
        offset = entity.get("offset")
        span = entity.get("length")
        if kind not in _ALLOWED_ENTITY_TYPES:
            continue
        try:
            offset = int(offset)
            span = int(span)
        except Exception:
            continue
        if offset < 0 or span < 1:
            continue
        if (offset + span) > max(0, int(length)):
            continue
        entry = {"type": kind, "offset": offset, "length": span}
        if kind == "text_link" and isinstance(entity.get("url"), str):
            entry["url"] = entity["url"]
        if kind == "text_mention" and entity.get("user") is not None:
            entry["user"] = entity["user"]
        if kind == "pre" and isinstance(entity.get("language"), str):
            entry["language"] = entity["language"]
        if kind == "custom_emoji" and isinstance(entity.get("custom_emoji_id"), str):
            entry["custom_emoji_id"] = entity["custom_emoji_id"]
        result.append(entry)
    if entities and not result:
        channel.emit(logging.DEBUG, LogCode.EXTRA_UNKNOWN_DROPPED, note="entities_dropped_all")
    return result

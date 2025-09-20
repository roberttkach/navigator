from __future__ import annotations

import logging
import warnings
from typing import Any, Dict, List

from ..log.emit import jlog
from ...domain.log.code import LogCode

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


def sanitize(entities: Any, text_len: int) -> List[Dict[str, Any]]:
    out: List[Dict[str, Any]] = []
    if not isinstance(entities, list):
        return out
    for e in entities:
        if not isinstance(e, dict):
            continue
        t = e.get("type")
        off = e.get("offset")
        ln = e.get("length")
        if t not in _ALLOWED_ENTITY_TYPES:
            continue
        try:
            off_i = int(off)
            ln_i = int(ln)
        except Exception:
            continue
        if off_i < 0 or ln_i < 1:
            continue
        if (off_i + ln_i) > max(0, int(text_len)):
            continue
        cleaned = {"type": t, "offset": off_i, "length": ln_i}
        if t == "text_link" and isinstance(e.get("url"), str):
            cleaned["url"] = e["url"]
        if t == "text_mention" and e.get("user") is not None:
            cleaned["user"] = e["user"]
        if t == "pre" and isinstance(e.get("language"), str):
            cleaned["language"] = e["language"]
        if t == "custom_emoji" and isinstance(e.get("custom_emoji_id"), str):
            cleaned["custom_emoji_id"] = e["custom_emoji_id"]
        out.append(cleaned)
    if entities and not out:
        jlog(logging.getLogger(__name__), logging.DEBUG, LogCode.EXTRA_UNKNOWN_DROPPED, note="entities_dropped_all")
    return out


def validate_entities(entities: Any, text_len: int) -> List[Dict[str, Any]]:
    warnings.warn("validate_entities is deprecated; use sanitize", DeprecationWarning, stacklevel=2)
    return sanitize(entities, text_len)

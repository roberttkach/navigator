from __future__ import annotations

from typing import Dict, Any, Set

from aiogram.types import FSInputFile, BufferedInputFile, URLInputFile

from ...domain.error import ExtraKeyForbidden

ALLOWED_TEXT = {"mode", "entities", "message_effect_id"}
ALLOWED_CAPTION_TEXT = {"mode", "entities", "message_effect_id"}
ALLOWED_MEDIA_EXTRA = {
    "spoiler",
    "show_caption_above_media",
    "start",
    "thumb",
    "title",
    "performer",
    "duration",
    "width",
    "height",
    "cover",
    "supports_streaming",
}


def audit(extra: Dict[str, Any] | None, allowed: Set[str]) -> None:
    if not extra:
        return
    keys = set(extra.keys())
    if not keys.issubset(set(allowed)):
        raise ExtraKeyForbidden()
    if "spoiler" in extra and not isinstance(extra["spoiler"], bool):
        raise ExtraKeyForbidden()
    if "show_caption_above_media" in extra and not isinstance(extra["show_caption_above_media"], bool):
        raise ExtraKeyForbidden()
    if "start" in extra:
        st = extra["start"]
        if not isinstance(st, int) or st < 0:
            raise ExtraKeyForbidden()
    if "duration" in extra:
        du = extra["duration"]
        if not isinstance(du, int) or du < 0:
            raise ExtraKeyForbidden()
    if "width" in extra:
        w = extra["width"]
        if not isinstance(w, int) or w < 0:
            raise ExtraKeyForbidden()
    if "height" in extra:
        h = extra["height"]
        if not isinstance(h, int) or h < 0:
            raise ExtraKeyForbidden()
    if "title" in extra and not isinstance(extra["title"], str):
        raise ExtraKeyForbidden()
    if "performer" in extra and not isinstance(extra["performer"], str):
        raise ExtraKeyForbidden()
    if "thumb" in extra:
        cv = extra["thumb"]
        if not isinstance(cv, (FSInputFile, BufferedInputFile, URLInputFile, str)):
            raise ExtraKeyForbidden()
    if "cover" in extra:
        cv = extra["cover"]
        if not isinstance(cv, (FSInputFile, BufferedInputFile, URLInputFile, str)):
            raise ExtraKeyForbidden()
    if "supports_streaming" in extra and not isinstance(extra["supports_streaming"], bool):
        raise ExtraKeyForbidden()
    if "message_effect_id" in extra and not isinstance(extra["message_effect_id"], str):
        raise ExtraKeyForbidden()

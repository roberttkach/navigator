"""Utilities for sanitizing history message extras before persistence."""

from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ...log.emit import jlog
from ...util.entities import validate_entities
from ....domain.log.code import LogCode

logger = logging.getLogger(__name__)

_ALLOWED_EXTRA_KEYS = {
    "mode",
    "entities",
    "spoiler",
    "show_caption_above_media",
    "start",
    "message_effect_id",
    "title",
    "performer",
    "duration",
    "width",
    "height",
    "has_thumb",
}


def sanitize_extra(extra: Any, *, text_len: int) -> Optional[Dict[str, Any]]:
    """Validate and normalize a history entry ``extra`` payload.

    The sanitizer mirrors the behaviour that historically lived in the storage
    layer: it keeps only JSON-serialisable fields, validates entities against the
    provided text length and tracks whether a thumbnail was supplied.
    """

    if not isinstance(extra, dict):
        return None

    unknown = sorted(k for k in extra.keys() if k not in _ALLOWED_EXTRA_KEYS)
    cleaned: Dict[str, Any] = {k: extra[k] for k in _ALLOWED_EXTRA_KEYS if k in extra}

    if extra.get("thumb") is not None:
        cleaned["has_thumb"] = True

    if "entities" in cleaned:
        valid_entities = validate_entities(cleaned.get("entities"), text_len)
        if valid_entities:
            cleaned["entities"] = valid_entities
        else:
            cleaned.pop("entities", None)

    if unknown:
        jlog(logger, logging.DEBUG, LogCode.EXTRA_UNKNOWN_DROPPED, filtered_keys=unknown)

    return cleaned or None


__all__ = ["sanitize_extra"]

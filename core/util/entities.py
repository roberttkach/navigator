"""Provide sanitizers for Telegram entity metadata."""

from __future__ import annotations

import logging
from typing import Any, Callable, Dict, List, Mapping, Tuple, cast

from ..telemetry import LogCode, Telemetry

EntityDict = Dict[str, Any]
EntityMapping = Mapping[str, Any]
OptionalFieldRule = Tuple[str, Callable[[Any], bool]]


def _is_str(value: Any) -> bool:
    """Return ``True`` when ``value`` is a string instance."""

    return isinstance(value, str)


def _is_present(value: Any) -> bool:
    """Return ``True`` when ``value`` is present (not ``None``)."""

    return value is not None


_ALLOWED_ENTITY_TYPES = frozenset(
    {
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
)

_OPTIONAL_FIELD_RULES: Dict[str, Tuple[OptionalFieldRule, ...]] = {
    "text_link": (("url", _is_str),),
    "text_mention": (("user", _is_present),),
    "pre": (("language", _is_str),),
    "custom_emoji": (("custom_emoji_id", _is_str),),
}


def sanitize(
        entities: Any,
        length: int,
        *,
        telemetry: Telemetry | None = None,
) -> List[EntityDict]:
    """Return sanitized message entities limited by the given length."""

    channel = telemetry.channel(__name__) if telemetry else None
    limit = _normalize_limit(length)
    sanitized = _sanitize_collection(entities, limit)

    if entities and not sanitized and channel is not None:
        channel.emit(
            logging.DEBUG,
            LogCode.EXTRA_UNKNOWN_DROPPED,
            note="entities_dropped_all",
        )

    return sanitized


def _sanitize_collection(entities: Any, limit: int) -> List[EntityDict]:
    """Return sanitized entity objects extracted from ``entities`` input."""

    if not isinstance(entities, list):
        return []

    sanitized: List[EntityDict] = []
    for entity in entities:
        data = _sanitize_entity(entity, limit)
        if data is not None:
            sanitized.append(data)
    return sanitized


def _sanitize_entity(entity: Any, limit: int) -> EntityDict | None:
    """Sanitize a single entity mapping, returning ``None`` if invalid."""

    if not isinstance(entity, dict):
        return None

    kind_value = entity.get("type")
    if kind_value not in _ALLOWED_ENTITY_TYPES:
        return None

    kind = cast(str, kind_value)
    span = _extract_span(entity, limit)
    if span is None:
        return None

    offset, length = span
    payload: EntityDict = {"type": kind, "offset": offset, "length": length}
    payload.update(_collect_optional_fields(kind, entity))
    return payload


def _extract_span(entity: EntityMapping, limit: int) -> Tuple[int, int] | None:
    """Extract a valid ``(offset, length)`` pair constrained by ``limit``."""

    try:
        offset = int(entity.get("offset"))
        span = int(entity.get("length"))
    except (TypeError, ValueError):
        return None

    if offset < 0 or span < 1:
        return None

    if offset + span > limit:
        return None

    return offset, span


def _collect_optional_fields(kind: str, entity: EntityMapping) -> EntityDict:
    """Collect optional attributes recognised for the provided entity kind."""

    extracted: EntityDict = {}
    rules = _OPTIONAL_FIELD_RULES.get(kind, ())
    for field, predicate in rules:
        value = entity.get(field)
        if predicate(value):
            extracted[field] = value
    return extracted


def _normalize_limit(length: int) -> int:
    """Return a non-negative integer limit derived from ``length`` argument."""

    try:
        return max(0, int(length))
    except (TypeError, ValueError):
        return 0

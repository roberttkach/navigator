"""Telegram-specific entity schema and sanitizer helpers."""

from __future__ import annotations

from typing import Any

from navigator.core.util.entities import (
    EntitySanitizer,
    EntitySchema,
    OptionalFieldRule,
)


def _is_str(value: Any) -> bool:
    """Return ``True`` when ``value`` is a string instance."""

    return isinstance(value, str)


def _is_present(value: Any) -> bool:
    """Return ``True`` when ``value`` is present (not ``None``)."""

    return value is not None


_OPTIONAL_RULES: dict[str, tuple[OptionalFieldRule, ...]] = {
    "text_link": (("url", _is_str),),
    "text_mention": (("user", _is_present),),
    "pre": (("language", _is_str),),
    "custom_emoji": (("custom_emoji_id", _is_str),),
}

TELEGRAM_ENTITY_SCHEMA = EntitySchema(
    allowed_types=(
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
    ),
    optional_fields=_OPTIONAL_RULES,
)

TELEGRAM_ENTITY_SANITIZER = EntitySanitizer(TELEGRAM_ENTITY_SCHEMA)


__all__ = [
    "TELEGRAM_ENTITY_SCHEMA",
    "TELEGRAM_ENTITY_SANITIZER",
]


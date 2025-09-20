"""Telegram presentation lexicon helper."""
from __future__ import annotations

from typing import Dict

_LEXICON: Dict[str, Dict[str, str]] = {
    "prev_not_found": {
        "en": "⚠️ Previous state not found.",
        "ru": "⚠️ Предыдущий экран не найден.",
    },
    "inline_unsupported": {
        "en": "⚠️ This screen is not available in an inline message.",
        "ru": "⚠️ Этот экран недоступен в инлайн-сообщении.",
    },
    "back": {
        "en": "« Back",
        "ru": "« Назад",
    },
}


def lexeme(key: str, lang: str = "en") -> str:
    """Return a localized lexeme for Telegram presentation."""
    lang_norm = (lang or "en").split("-")[0].lower()
    d = _LEXICON.get(key, {})
    return d.get(lang_norm) or d.get("en") or ""

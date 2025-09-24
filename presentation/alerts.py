from __future__ import annotations

from typing import Mapping

from ..core.value.message import Scope

_Lexicon = {
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


def lexeme(key: str, locale: str | None = None) -> str:
    table: Mapping[str, Mapping[str, str]] = _Lexicon
    values = table.get(key, {})
    lang = (locale or "en").split("-")[0].lower()
    return values.get(lang) or values.get("en") or ""


def prev_not_found(scope: Scope) -> str:
    return lexeme("prev_not_found", scope.lang)


def inline_unsupported(scope: Scope) -> str:
    return lexeme("inline_unsupported", scope.lang)


def back_label(locale: str | None) -> str:
    return lexeme("back", locale)


__all__ = ["lexeme", "prev_not_found", "inline_unsupported", "back_label"]

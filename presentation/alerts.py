from __future__ import annotations

from typing import Mapping

from ..core.value.message import Scope

LEXICON = {
    "missing": {
        "en": "⚠️ Previous state not found.",
        "ru": "⚠️ Предыдущий экран не найден.",
    },
    "barred": {
        "en": "⚠️ This screen is not available in an inline message.",
        "ru": "⚠️ Этот экран недоступен в инлайн-сообщении.",
    },
    "back": {
        "en": "« Back",
        "ru": "« Назад",
    },
}


def lexeme(key: str, locale: str | None = None) -> str:
    table: Mapping[str, Mapping[str, str]] = LEXICON
    values = table.get(key, {})
    lang = (locale or "en").split("-")[0].lower()
    return values.get(lang) or values.get("en") or ""


def missing(scope: Scope) -> str:
    return lexeme("missing", scope.lang)


def barred(scope: Scope) -> str:
    return lexeme("barred", scope.lang)


def revert(locale: str | None) -> str:
    return lexeme("back", locale)


__all__ = ["lexeme", "missing", "barred", "revert"]

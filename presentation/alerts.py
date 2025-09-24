from __future__ import annotations

from ..core.value.message import Scope

_LEXICON = {
    "prev_not_found": {
        "en": "⚠️ Previous state not found.",
        "ru": "⚠️ Предыдущий экран не найден.",
    },
}


def prev_not_found(scope: Scope) -> str:
    lang = (scope.lang or "en").split("-")[0].lower()
    lexemes = _LEXICON["prev_not_found"]
    return lexemes.get(lang) or lexemes.get("en") or ""


__all__ = ["prev_not_found"]

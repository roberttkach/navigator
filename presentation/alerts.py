from __future__ import annotations

from ..domain.value.message import Scope
from .telegram.lexicon import lexeme


def prev_not_found(scope: Scope) -> str:
    return lexeme("prev_not_found", scope.lang or "en")


__all__ = ["prev_not_found"]

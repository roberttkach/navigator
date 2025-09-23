from __future__ import annotations

from ..domain.port.message import AlertPayload
from ..domain.value.message import Scope
from .telegram.lexicon import lexeme


def prev_not_found(scope: Scope) -> AlertPayload:
    return AlertPayload(text=lexeme("prev_not_found", scope.lang or "en"))


__all__ = ["prev_not_found"]

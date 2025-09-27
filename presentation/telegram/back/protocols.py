"""Protocols shared across telegram retreat components."""

from __future__ import annotations

from collections.abc import Callable
from typing import Protocol

from navigator.core.contracts.back import NavigatorBackContext


class RetreatHistory(Protocol):
    async def back(self, context: NavigatorBackContext) -> None: ...


class NavigatorBack(Protocol):
    history: RetreatHistory


Translator = Callable[[str, str], str]


class RetreatFailureTranslator(Protocol):
    """Translate domain errors into retreat specific failure notes."""

    def translate(self, error: Exception) -> str | None:
        """Return a failure note understood by presentation workflow."""


__all__ = [
    "NavigatorBack",
    "RetreatFailureTranslator",
    "RetreatHistory",
    "Translator",
]

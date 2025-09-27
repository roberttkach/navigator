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


class RetreatFailureNotes(Protocol):
    """Map workflow failure notes to presentation translation keys."""

    def present(self, note: str | None) -> str:
        """Return translation key representing ``note``."""


class RetreatFailureTranslator(Protocol):
    """Translate domain errors into retreat specific failure notes."""

    def translate(self, error: Exception) -> str | None:
        """Return a failure note understood by presentation workflow."""


__all__ = [
    "NavigatorBack",
    "RetreatFailureTranslator",
    "RetreatFailureNotes",
    "RetreatHistory",
    "Translator",
]

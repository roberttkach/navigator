"""Translate navigator errors into retreat failure notes."""

from __future__ import annotations

from typing import Iterable

from navigator.core.error import (
    HistoryEmpty,
    InlineUnsupported,
    NavigatorError,
    StateNotFound,
)


class RetreatFailureResolver:
    """Resolve workflow errors into retreat failure identifiers."""

    _DEFAULT_NOTE = "generic"

    def __init__(self, *, recognized: Iterable[type[NavigatorError]] | None = None) -> None:
        self._recognized = tuple(recognized or (HistoryEmpty, StateNotFound, InlineUnsupported))

    def translate(self, error: Exception) -> str | None:
        """Return a failure note for ``error`` when recognized."""

        if not isinstance(error, NavigatorError):
            return None
        for kind in self._recognized:
            if isinstance(error, kind):
                return self._note_for(kind, error)
        return self._DEFAULT_NOTE

    def _note_for(
        self,
        kind: type[NavigatorError],
        error: NavigatorError,
    ) -> str:
        if kind is HistoryEmpty:
            return "history_empty"
        if kind is StateNotFound:
            return "state_not_found"
        if kind is InlineUnsupported:
            return "barred"
        return str(error) or self._DEFAULT_NOTE


__all__ = ["RetreatFailureResolver"]

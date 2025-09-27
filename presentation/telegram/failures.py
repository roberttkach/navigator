"""Failure translator factories for telegram presentation layer."""

from __future__ import annotations

from typing import Mapping

from navigator.app.service.retreat_failure import RetreatFailureResolver

from .back.protocols import RetreatFailureNotes, RetreatFailureTranslator


class RetreatFailureNoticePresenter:
    """Map domain-specific failure notes to presentation translation keys."""

    def __init__(
        self,
        *,
        mapping: Mapping[str, str] | None = None,
        fallback: str = "missing",
    ) -> None:
        self._mapping = dict(mapping or {"barred": "barred"})
        self._fallback = fallback

    def present(self, note: str | None) -> str:
        if not note:
            return self._fallback
        return self._mapping.get(note, self._fallback)


def default_retreat_failure_translator() -> RetreatFailureTranslator:
    """Return the default failure translator wired to application resolver."""

    return RetreatFailureResolver()


def default_retreat_failure_notes() -> RetreatFailureNotes:
    """Return the default mapping from domain notes to presentation keys."""

    return RetreatFailureNoticePresenter()


__all__ = [
    "default_retreat_failure_notes",
    "default_retreat_failure_translator",
    "RetreatFailureNoticePresenter",
]

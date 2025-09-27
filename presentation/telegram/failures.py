"""Failure translator factories for telegram presentation layer."""

from __future__ import annotations

from navigator.app.service.retreat_failure import (
    RetreatFailureNoticePresenter,
    RetreatFailureResolver,
)

from .back.protocols import RetreatFailureNotes, RetreatFailureTranslator


def default_retreat_failure_translator() -> RetreatFailureTranslator:
    """Return the default failure translator wired to application resolver."""

    return RetreatFailureResolver()


def default_retreat_failure_notes() -> RetreatFailureNotes:
    """Return the default mapping from domain notes to presentation keys."""

    return RetreatFailureNoticePresenter()


__all__ = [
    "default_retreat_failure_notes",
    "default_retreat_failure_translator",
]

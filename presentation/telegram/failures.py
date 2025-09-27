"""Failure translator factories for telegram presentation layer."""

from __future__ import annotations

from navigator.app.service.retreat_failure import RetreatFailureResolver

from .back.protocols import RetreatFailureTranslator


def default_retreat_failure_translator() -> RetreatFailureTranslator:
    """Return the default failure translator wired to application resolver."""

    return RetreatFailureResolver()


__all__ = ["default_retreat_failure_translator"]

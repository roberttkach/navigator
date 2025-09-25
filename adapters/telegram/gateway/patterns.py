"""Canonical Bot API error message fragments used by the Telegram gateway.

The official cloud Bot API (7.x) responds with English descriptions only, and
aiogram 3.22.0 surfaces these descriptions verbatim. We therefore keep a small
set of English fragments that are known to precede the explanatory part of the
errors. See https://core.telegram.org/bots/api#making-requests and
https://docs.aiogram.dev/en/v3.22.0/api/exceptions/ for details.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ErrorPatterns:
    """Container with normalized message fragments for a Bot API error."""

    patterns: tuple[str, ...]

    @classmethod
    def collect(cls, *phrases: str) -> ErrorPatterns:
        normalized = tuple(phrase.lower() for phrase in phrases)
        return cls(patterns=normalized)

    def matches(self, message: str) -> bool:
        """Return ``True`` if *message* contains one of the stored fragments."""

        lowered = message.lower()
        return any(fragment in lowered for fragment in self.patterns)


NOT_MODIFIED = ErrorPatterns.collect("message is not modified")

EDIT_FORBIDDEN = ErrorPatterns.collect(
    "message can't be edited",
    "bot can't edit message",
    "message is not editable",
    "message can be edited only within 48 hours",
)


__all__ = ["ErrorPatterns", "NOT_MODIFIED", "EDIT_FORBIDDEN"]

"""Prepare inline editing candidates from preserved payloads."""
from __future__ import annotations

from navigator.core.entity.history import Message
from navigator.core.value.content import Payload

from ...store import preserve


class InlineCandidateBuilder:
    """Prepare preserved payloads suitable for inline editing."""

    def create(self, payload: Payload, tail: Message | None) -> Payload:
        entry = preserve(payload, tail)
        if getattr(entry, "group", None):
            return entry.morph(media=entry.group[0], group=None)
        return entry


__all__ = ["InlineCandidateBuilder"]

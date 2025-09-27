"""Helpers calculating markers for inline tail history."""
from __future__ import annotations

from collections.abc import Sequence

from navigator.core.entity.history import Entry


class TailInlineMarker:
    """Derive marker identifiers from stored history snapshots."""

    @staticmethod
    def latest(history: Sequence[Entry]) -> int | None:
        if not history:
            return None
        tail = history[-1]
        if not tail.messages:
            return None
        return int(tail.messages[0].id)


__all__ = ["TailInlineMarker"]

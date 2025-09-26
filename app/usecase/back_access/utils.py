"""Utility helpers shared across rewind components."""
from __future__ import annotations

from collections.abc import Iterable, Sequence

from navigator.core.entity.history import Entry


def trim(history: Sequence[Entry]) -> Iterable[Entry]:
    """Yield history entries without the latest snapshot."""

    yield from history[:-1]

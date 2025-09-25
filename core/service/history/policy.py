"""Trim stored history entries according to configured policies."""

from __future__ import annotations

from typing import List

from ...entity.history import Entry

HistoryList = List[Entry]


def prune(history: HistoryList, limit: int) -> HistoryList:
    """Return history trimmed to ``limit`` while preserving the root."""

    maximum = _coerce_limit(limit)
    if len(history) <= maximum:
        return history

    overflow = len(history) - maximum
    if history and getattr(history[0], "root", False):
        return _preserve_root(history, overflow)
    return history[overflow:]


def _coerce_limit(limit: int) -> int:
    """Coerce ``limit`` into a non-negative integer bound."""

    try:
        return max(0, int(limit))
    except (TypeError, ValueError):
        return 0


def _preserve_root(history: HistoryList, overflow: int) -> HistoryList:
    """Retain the root entry while trimming ``overflow`` items."""

    preserved = history[0]
    start = min(len(history), 1 + overflow)
    return [preserved, *history[start:]]

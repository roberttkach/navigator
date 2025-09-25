"""Trim stored history entries according to configured policies."""

from __future__ import annotations

from typing import List

from ...entity.history import Entry

HistoryList = List[Entry]


def prune(history: HistoryList, limit: int) -> HistoryList:
    """Return history trimmed to ``limit`` while preserving the root."""

    try:
        maximum = max(0, int(limit))
    except (TypeError, ValueError):
        maximum = 0
    if len(history) <= maximum:
        return history

    overflow = len(history) - maximum
    if history and getattr(history[0], "root", False):
        preserved = history[0]
        start = min(len(history), 1 + overflow)
        return [preserved, *history[start:]]

    return history[overflow:]

from typing import List

from ...entity.history import Entry


def prune(history: List[Entry], limit: int) -> List[Entry]:
    if len(history) <= limit:
        return history
    overflow = len(history) - limit
    if history and getattr(history[0], "root", False):
        start = 1 + overflow
        return [history[0]] + history[start:]
    return history[overflow:]

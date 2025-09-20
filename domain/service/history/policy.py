from typing import List

from ...entity.history import Entry


def trim(history: List[Entry], max_len: int) -> List[Entry]:
    if len(history) <= max_len:
        return history
    overflow = len(history) - max_len
    if history and getattr(history[0], "root", False):
        cut_from = 1 + overflow
        return [history[0]] + history[cut_from:]
    return history[overflow:]

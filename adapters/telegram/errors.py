from __future__ import annotations

from typing import Iterator

from .gateway.patterns import ErrorPatterns

_DISMISSIBLE_ERRORS = ErrorPatterns.collect(
    "message to delete not found",
    "message can't be deleted",
    "message cant be deleted",
    "cannot be deleted",
    "cannot delete",
    "cant delete",
    "can't be deleted for everyone",
    "cant be deleted for everyone",
    "message is too old",
    "too old",
    "not enough rights",
    "not enough rights to delete",
    "already deleted",
    "paid post",
    "is_paid_post",
    "must not be deleted for 24 hours",
)


def dismissible(message: str) -> bool:
    return _DISMISSIBLE_ERRORS.matches(message)


def _cascade(error: Exception) -> Iterator[Exception]:
    seen = set()
    stack = [error]
    while stack:
        current = stack.pop()
        if not current:
            continue
        if id(current) in seen:
            continue
        seen.add(id(current))
        yield current
        cause = getattr(current, "__cause__", None)
        context = getattr(current, "__context__", None)
        if cause:
            stack.append(cause)
        if context:
            stack.append(context)


def excusable(error: Exception) -> bool:
    for current in _cascade(error):
        message = (getattr(current, "message", "") or str(current)).lower()
        if dismissible(message):
            return True
    return False

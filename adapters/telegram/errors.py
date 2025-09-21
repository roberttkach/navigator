from typing import Iterator


def dismissible(message: str) -> bool:
    return (
        "message to delete not found" in message
        or "message can't be deleted" in message
        or "message cant be deleted" in message
        or "cannot be deleted" in message
        or "cannot delete" in message
        or "cant delete" in message
        or "can't be deleted for everyone" in message
        or "cant be deleted for everyone" in message
        or "message is too old" in message
        or "too old" in message
        or "not enough rights" in message
        or "not enough rights to delete" in message
        or "already deleted" in message
        or "уже удалено" in message
        or "недостаточно прав" in message
        or "paid post" in message
        or "is_paid_post" in message
        or "must not be deleted for 24 hours" in message
    )


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

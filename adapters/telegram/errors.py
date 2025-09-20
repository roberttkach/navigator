from typing import Iterator


def soft_ignorable(msg_lc: str) -> bool:
    return (
            "message to delete not found" in msg_lc
            or "message can't be deleted" in msg_lc
            or "message cant be deleted" in msg_lc
            or "cannot be deleted" in msg_lc
            or "cannot delete" in msg_lc
            or "cant delete" in msg_lc
            or "can't be deleted for everyone" in msg_lc
            or "cant be deleted for everyone" in msg_lc
            or "message is too old" in msg_lc
            or "too old" in msg_lc
            or "not enough rights" in msg_lc
            or "not enough rights to delete" in msg_lc
            or "already deleted" in msg_lc
            or "уже удалено" in msg_lc
            or "недостаточно прав" in msg_lc
            or "paid post" in msg_lc
            or "is_paid_post" in msg_lc
            or "must not be deleted for 24 hours" in msg_lc
    )


def _iter_exc_chain(e: Exception) -> Iterator[Exception]:
    seen = set()
    stack = [e]
    while stack:
        ex = stack.pop()
        if not ex:
            continue
        if id(ex) in seen:
            continue
        seen.add(id(ex))
        yield ex
        cause = getattr(ex, "__cause__", None)
        ctx = getattr(ex, "__context__", None)
        if cause:
            stack.append(cause)
        if ctx:
            stack.append(ctx)


def any_soft_ignorable_exc(e: Exception) -> bool:
    for ex in _iter_exc_chain(e):
        msg = (getattr(ex, "message", "") or str(ex)).lower()
        if soft_ignorable(msg):
            return True
    return False

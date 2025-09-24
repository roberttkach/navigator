from collections.abc import Iterable


def order(ids: Iterable[int]) -> list[int]:
    return sorted({int(x) for x in ids or []})

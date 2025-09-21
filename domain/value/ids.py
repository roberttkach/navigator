from collections.abc import Iterable


def dedupe(ids: Iterable[int], sort: bool = False) -> list[int]:
    if sort:
        return order(ids)
    seen = set()
    out = []
    for x in ids or []:
        i = int(x)
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def order(ids: Iterable[int]) -> list[int]:
    return sorted({int(x) for x in ids or []})

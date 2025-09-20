from typing import Iterable, List


def unique_ids(ids: Iterable[int], sort: bool = False) -> List[int]:
    if sort:
        return unique_sorted(ids)
    seen = set()
    out = []
    for x in ids or []:
        i = int(x)
        if i not in seen:
            seen.add(i)
            out.append(i)
    return out


def unique_sorted(ids: Iterable[int]) -> List[int]:
    return sorted({int(x) for x in ids or []})

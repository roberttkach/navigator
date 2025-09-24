from __future__ import annotations

import typing
from typing import Protocol, Set


@typing.runtime_checkable
class Limits(Protocol):
    def text_max(self) -> int:
        ...

    def caption_max(self) -> int:
        ...

    def album_floor(self) -> int:
        ...

    def album_ceiling(self) -> int:
        ...

    def album_blend(self) -> Set[str]:
        ...


__all__ = ["Limits"]

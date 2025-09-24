from __future__ import annotations

import typing
from typing import Protocol, Set


@typing.runtime_checkable
class Limits(Protocol):
    def textlimit(self) -> int:
        ...

    def captionlimit(self) -> int:
        ...

    def groupmin(self) -> int:
        ...

    def groupmax(self) -> int:
        ...

    def groupmix(self) -> Set[str]:
        ...


__all__ = ["Limits"]

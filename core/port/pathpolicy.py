from __future__ import annotations

import typing
from typing import Protocol


@typing.runtime_checkable
class MediaPathPolicy(Protocol):
    def admissible(self, path: object, *, inline: bool) -> bool:
        ...

    def adapt(self, path: object, *, native: bool) -> object:
        ...


__all__ = ["MediaPathPolicy"]

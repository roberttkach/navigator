from __future__ import annotations

import typing
from typing import Protocol, Callable, Awaitable

from ..value.content import Payload

ViewForge = Callable[..., Awaitable[Payload]]


@typing.runtime_checkable
class ViewLedger(Protocol):
    def get(self, key: str) -> ViewForge: ...

    def has(self, key: str) -> bool: ...


__all__ = ["ViewForge", "ViewLedger"]

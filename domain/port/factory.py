from __future__ import annotations

from typing import Protocol, Callable, Awaitable, runtime_checkable

from ..value.content import Payload

ViewForge = Callable[..., Awaitable[Payload]]


@runtime_checkable
class ViewLedger(Protocol):
    def get(self, key: str) -> ViewForge: ...

    def has(self, key: str) -> bool: ...


__all__ = ["ViewForge", "ViewLedger"]

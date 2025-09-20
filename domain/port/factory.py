from __future__ import annotations

from typing import Protocol, Callable, Awaitable, runtime_checkable

from ..value.content import Payload

ViewFactory = Callable[..., Awaitable[Payload]]


@runtime_checkable
class ViewFactoryRegistry(Protocol):
    def get(self, key: str) -> ViewFactory: ...

    def has(self, key: str) -> bool: ...


__all__ = ["ViewFactory", "ViewFactoryRegistry"]

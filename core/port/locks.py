from __future__ import annotations

import typing
from typing import Protocol


@typing.runtime_checkable
class Lock(Protocol):
    async def acquire(self) -> bool:
        ...

    def release(self) -> None:
        ...

    async def untether(self) -> None:
        ...

    def locked(self) -> bool:
        ...


@typing.runtime_checkable
class LockProvider(Protocol):
    def latch(self, key: tuple[object, object | None]) -> Lock:
        ...


__all__ = ["Lock", "LockProvider"]

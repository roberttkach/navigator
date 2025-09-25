from __future__ import annotations

import asyncio
from typing import Dict, Tuple

from navigator.core.port.locks import Lock, LockProvider


class _LockWrapper(Lock):
    def __init__(self) -> None:
        self._lock = asyncio.Lock()

    async def acquire(self) -> bool:
        await self._lock.acquire()
        return True

    def release(self) -> None:
        self._lock.release()

    async def untether(self) -> None:
        if self._lock.locked():
            self._lock.release()

    def locked(self) -> bool:
        return self._lock.locked()


class MemoryLatch(LockProvider):
    def __init__(self) -> None:
        self._locks: Dict[Tuple[object, object | None], _LockWrapper] = {}

    def latch(self, key: tuple[object, object | None]) -> Lock:
        if key not in self._locks:
            self._locks[key] = _LockWrapper()
        return self._locks[key]


__all__ = ["MemoryLatch"]

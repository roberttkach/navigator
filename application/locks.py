from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from weakref import WeakValueDictionary

"""
Ограничение: InMemory реализация процесс-локальная. Для межпроцессной синхронизации
используйте set_lock_provider() с адаптером из инфраструктурного слоя.
Ключ блокировки: (inline_id|chat, biz_id).
"""


class ScopeLike(Protocol):
    inline_id: object | None
    chat: object | None
    biz_id: object | None


def _key(scope: ScopeLike) -> tuple[object | None, object | None]:
    return (
        getattr(scope, "inline_id", None) or getattr(scope, "chat", None),
        getattr(scope, "biz_id", None),
    )


@runtime_checkable
class _LockLike(Protocol):
    async def acquire(self) -> bool: ...

    def release(self) -> None: ...

    async def release_async(self) -> None: ...

    def locked(self) -> bool: ...


@dataclass
class LockBox:
    lock: _LockLike


class LockProvider(Protocol):
    def box_for(self, key: tuple[object, object | None]) -> LockBox: ...


class _MemLockAdapter:
    def __init__(self) -> None:
        self._l = asyncio.Lock()

    async def acquire(self) -> bool:
        await self._l.acquire()
        return True

    def release(self) -> None:
        self._l.release()

    async def release_async(self) -> None:
        # asyncio.Lock.release() синхронный; для совместимости оставляем await-обёртку
        self._l.release()

    def locked(self) -> bool:
        return self._l.locked()


class InMemoryLockProvider:
    def __init__(self) -> None:
        self._locks: WeakValueDictionary[
            tuple[object, object | None], LockBox
        ] = WeakValueDictionary()

    def box_for(self, key: tuple[object, object | None]) -> LockBox:  # type: ignore[override]
        box = self._locks.get(key)
        if box is None:
            box = LockBox(lock=_MemLockAdapter())
            self._locks[key] = box
        return box


_PROVIDER: list[LockProvider] = [InMemoryLockProvider()]


def _current_provider() -> LockProvider:
    return _PROVIDER[0]


def set_lock_provider(p: LockProvider) -> None:
    _PROVIDER[0] = p


class Guard:
    def __init__(self, scope: ScopeLike) -> None:
        k = _key(scope)
        self._box = _current_provider().box_for(k)

    async def __aenter__(self) -> None:
        await self._box.lock.acquire()

    async def __aexit__(
        self, exc_type: object, exc: object, traceback: object
    ) -> None:
        rel = getattr(self._box.lock, "release_async", None)
        if rel:
            await rel()
        else:
            self._box.lock.release()


def guard(scope: ScopeLike) -> Guard:
    return Guard(scope)


__all__ = [
    "LockBox",
    "LockProvider",
    "InMemoryLockProvider",
    "ScopeLike",
    "Guard",
    "guard",
    "set_lock_provider",
]

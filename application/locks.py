from __future__ import annotations

from __future__ import annotations

import asyncio
import warnings
from dataclasses import dataclass
from typing import Protocol, runtime_checkable
from weakref import WeakValueDictionary

"""
Ограничение: MemoryLocksmith процесс-локальная. Для межпроцессной синхронизации
используйте appoint() с адаптером из инфраструктурного слоя.
Ключ блокировки: (inline|chat, business).
"""


class ScopeForm(Protocol):
    inline: object | None
    chat: object | None
    business: object | None


def _key(scope: ScopeForm) -> tuple[object | None, object | None]:
    return (
        getattr(scope, "inline", None) or getattr(scope, "chat", None),
        getattr(scope, "business", None),
    )


@runtime_checkable
class _LatchLike(Protocol):
    async def acquire(self) -> bool: ...

    def release(self) -> None: ...

    async def untether(self) -> None: ...

    def locked(self) -> bool: ...


@dataclass
class Latch:
    lock: _LatchLike


class Locksmith(Protocol):
    def latch(self, key: tuple[object, object | None]) -> Latch: ...


class _LatchAdapter:
    def __init__(self) -> None:
        self._l = asyncio.Lock()

    async def acquire(self) -> bool:
        await self._l.acquire()
        return True

    def release(self) -> None:
        self._l.release()

    async def untether(self) -> None:
        # asyncio.Lock.release() синхронный; для совместимости оставляем await-обёртку
        self._l.release()

    def locked(self) -> bool:
        return self._l.locked()


class MemoryLocksmith:
    def __init__(self) -> None:
        self._locks: WeakValueDictionary[
            tuple[object, object | None], Latch
        ] = WeakValueDictionary()

    def latch(self, key: tuple[object, object | None]) -> Latch:  # type: ignore[override]
        latch = self._locks.get(key)
        if latch is None:
            latch = Latch(lock=_LatchAdapter())
            self._locks[key] = latch
        return latch


_PROVIDER: list[Locksmith] = [MemoryLocksmith()]


def _current() -> Locksmith:
    return _PROVIDER[0]


def appoint(p: Locksmith) -> None:
    _PROVIDER[0] = p


class Guard:
    def __init__(self, scope: ScopeForm) -> None:
        k = _key(scope)
        self._latch = _current().latch(k)

    async def __aenter__(self) -> None:
        await self._latch.lock.acquire()

    async def __aexit__(
        self, kind: object, exc: object, trace: object
    ) -> None:
        rel = getattr(self._latch.lock, "untether", None)
        if rel:
            await rel()
        else:
            self._latch.lock.release()


def guard(scope: ScopeForm) -> Guard:
    return Guard(scope)


__all__ = [
    "Latch",
    "Locksmith",
    "MemoryLocksmith",
    "ScopeForm",
    "Guard",
    "guard",
    "appoint",
]


# --- Legacy aliases -------------------------------------------------------

ScopeLike = ScopeForm
LockProvider = Locksmith


@dataclass
class LockBox(Latch):
    def __post_init__(self) -> None:  # pragma: no cover - compatibility shim
        warnings.warn("LockBox is deprecated; use Latch", DeprecationWarning, stacklevel=2)


class InMemoryLockProvider(MemoryLocksmith):
    def __init__(self) -> None:
        warnings.warn("InMemoryLockProvider is deprecated; use MemoryLocksmith", DeprecationWarning, stacklevel=2)
        super().__init__()


def reappoint(p: Locksmith) -> None:
    warnings.warn("set_lock_provider is deprecated; use appoint", DeprecationWarning, stacklevel=2)
    appoint(p)


__all__ += [
    "ScopeLike",
    "LockProvider",
    "LockBox",
    "InMemoryLockProvider",
    "reappoint",
]

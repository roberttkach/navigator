from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import Protocol, Tuple, runtime_checkable
from weakref import WeakValueDictionary

try:
    from redis.asyncio import Redis  # type: ignore
except Exception:  # pragma: no cover
    Redis = None  # type: ignore

"""
Ограничение: InMemory реализация процесс-локальная. Для межпроцессной синхронизации
используйте RedisLockProvider и configure_from_env().
Ключ блокировки: (inline_id|chat, biz_id).
"""


def _key(scope):
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
class _LockBox:
    lock: _LockLike


class LockProvider(Protocol):
    def box_for(self, key: Tuple[object, object | None]) -> _LockBox: ...


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
        self._locks: "WeakValueDictionary[tuple[object, object | None], _LockBox]" = WeakValueDictionary()

    def box_for(self, key: Tuple[object, object | None]) -> _LockBox:  # type: ignore[override]
        box = self._locks.get(key)
        if box is None:
            box = _LockBox(lock=_MemLockAdapter())
            self._locks[key] = box
        return box


class _AsyncLockAdapter:
    """
    Адаптер над асинхронным бэкендом блокировки с честным locked().
    holder._b должен предоставлять async acquire()/release().
    """

    def __init__(self, holder) -> None:
        self._h = holder
        self._locked = False

    async def acquire(self) -> bool:
        await self._h._b.acquire()
        self._locked = True
        return True

    def release(self) -> None:
        self._locked = False
        asyncio.get_running_loop().create_task(self._h._b.release())

    async def release_async(self) -> None:
        await self._h._b.release()
        self._locked = False

    def locked(self) -> bool:
        return bool(self._locked)


class RedisLockProvider:
    def __init__(self, url: str, ttl: float, blocking: float) -> None:
        if Redis is None:
            raise RuntimeError("redis package not installed")
        self._r = Redis.from_url(url)
        self._ttl = float(ttl)
        self._blocking = float(blocking)

    def box_for(self, key: Tuple[object, object | None]) -> _LockBox:  # type: ignore[override]
        name = f"nav:lock:{key[0]}:{key[1]}"

        class _RedisBox:
            def __init__(self, r, name, ttl, blocking):
                self._r = r
                self._name = name
                self._ttl = ttl
                self._blocking = blocking
                self._lock = None

            async def acquire(self):
                self._lock = self._r.lock(self._name, timeout=self._ttl, blocking_timeout=self._blocking)
                await self._lock.acquire()

            async def release(self):
                try:
                    if self._lock:
                        await self._lock.release()
                except Exception as e:
                    # Логируем предупреждение. Семантика Guard не меняется.
                    import logging
                    logging.getLogger(__name__).warning("redis_lock_release_failed: %s", type(e).__name__)

        box = _RedisBox(self._r, name, self._ttl, self._blocking)

        class _GuardCompat:
            def __init__(self, b):
                self._b = b

        g = _GuardCompat(box)
        return _LockBox(lock=_AsyncLockAdapter(g))


_provider: LockProvider = InMemoryLockProvider()


def set_lock_provider(p: LockProvider) -> None:
    global _provider
    _provider = p


def configure_from_env() -> None:
    mode = os.getenv("NAV_LOCKS", "memory").lower()
    if mode == "redis":
        url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
        ttl = float(os.getenv("NAV_LOCK_TTL", "20"))
        bt = float(os.getenv("NAV_LOCK_BLOCKING", "5"))
        set_lock_provider(RedisLockProvider(url, ttl, bt))


class Guard:
    def __init__(self, scope) -> None:
        k = _key(scope)
        self._box = _provider.box_for(k)

    async def __aenter__(self) -> None:
        await self._box.lock.acquire()

    async def __aexit__(self, *a) -> None:
        rel = getattr(self._box.lock, "release_async", None)
        if rel:
            await rel()
        else:
            self._box.lock.release()


def guard(scope):
    return Guard(scope)

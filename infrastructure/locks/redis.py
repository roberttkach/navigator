from __future__ import annotations

import asyncio
import logging
from typing import Any

try:
    from redis.asyncio import Redis
except Exception:  # pragma: no cover - optional dependency
    Redis = None

from domain.port.locks import Lock, LockProvider

logger = logging.getLogger(__name__)


class _RedisLock(Lock):
    def __init__(self, redis: Any, name: str, ttl: float, blocking: float) -> None:
        self._redis = redis
        self._name = name
        self._ttl = ttl
        self._blocking = blocking
        self._lock: Any | None = None
        self._held = False

    async def acquire(self) -> bool:
        self._lock = self._redis.lock(
            self._name,
            timeout=self._ttl,
            blocking_timeout=self._blocking,
        )
        await self._lock.acquire()
        self._held = True
        return True

    def release(self) -> None:
        if self._held and self._lock is not None:
            asyncio.get_running_loop().create_task(self.untether())

    async def untether(self) -> None:
        if not self._held or self._lock is None:
            return
        try:
            await self._lock.release()
        except Exception as exc:  # pragma: no cover - log but ignore
            logger.warning("redis_lock_release_failed: %s", type(exc).__name__)
        finally:
            self._held = False

    def locked(self) -> bool:
        return self._held


class RedisLockProvider(LockProvider):
    def __init__(self, url: str, *, ttl: float, blocking: float) -> None:
        if Redis is None:
            raise RuntimeError("redis package not installed")
        self._redis = Redis.from_url(url)
        self._ttl = float(ttl)
        self._blocking = float(blocking)

    def latch(self, key: tuple[object, object | None]) -> Lock:
        name = f"nav:lock:{key[0]}:{key[1]}"
        return _RedisLock(self._redis, name, self._ttl, self._blocking)


__all__ = ["RedisLockProvider"]

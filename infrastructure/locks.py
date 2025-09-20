from __future__ import annotations

import asyncio
import logging
import warnings
import os
from typing import TYPE_CHECKING, Any

try:
    from redis.asyncio import Redis  # type: ignore[attr-defined]
except Exception:  # pragma: no cover - optional dependency
    Redis = None  # type: ignore[assignment]

if TYPE_CHECKING:
    from redis.asyncio import Redis as RedisClient  # pragma: no cover
else:  # pragma: no cover
    RedisClient = Any

from ..application.locks import Latch, Locksmith, appoint

logger = logging.getLogger(__name__)


class _RedisLockAdapter:
    """Adapter that exposes redis lock through the application lock protocol."""

    def __init__(
        self, redis: RedisClient, name: str, ttl: float, blocking: float
    ) -> None:
        self._redis = redis
        self._name = name
        self._ttl = ttl
        self._blocking = blocking
        self._lock: Any | None = None
        self._locked = False

    async def acquire(self) -> bool:
        self._lock = self._redis.lock(
            self._name,
            timeout=self._ttl,
            blocking_timeout=self._blocking,
        )
        await self._lock.acquire()
        self._locked = True
        return True

    async def release_async(self) -> None:
        try:
            if self._lock:
                await self._lock.release()
        except Exception as exc:  # pragma: no cover - defensive logging
            logger.warning("redis_lock_release_failed: %s", type(exc).__name__)
        finally:
            self._locked = False

    def release(self) -> None:
        self._locked = False
        asyncio.get_running_loop().create_task(self.release_async())

    def locked(self) -> bool:
        return bool(self._locked)


class RedisLocksmith(Locksmith):
    """Distributed lock provider backed by redis."""

    def __init__(self, url: str, ttl: float, blocking: float) -> None:
        if Redis is None:  # pragma: no cover - optional dependency
            raise RuntimeError("redis package not installed")
        self._redis = Redis.from_url(url)
        self._ttl = float(ttl)
        self._blocking = float(blocking)

    def box_for(self, key: tuple[object, object | None]) -> Latch:  # type: ignore[override]
        name = f"nav:lock:{key[0]}:{key[1]}"
        adapter = _RedisLockAdapter(self._redis, name, self._ttl, self._blocking)
        return Latch(lock=adapter)


def configure_from_env() -> None:
    """Configure lock provider based on environment variables."""

    mode = os.getenv("NAV_LOCKS", "memory").lower()
    if mode != "redis":
        return
    url = os.getenv("REDIS_URL", "redis://localhost:6379/0")
    ttl = float(os.getenv("NAV_LOCK_TTL", "20"))
    blocking = float(os.getenv("NAV_LOCK_BLOCKING", "5"))
    appoint(RedisLocksmith(url, ttl, blocking))


class RedisLockProvider(RedisLocksmith):
    def __init__(self, url: str, ttl: float, blocking: float) -> None:
        warnings.warn("RedisLockProvider is deprecated; use RedisLocksmith", DeprecationWarning, stacklevel=2)
        super().__init__(url, ttl, blocking)


__all__ = ["RedisLocksmith", "RedisLockProvider", "configure_from_env"]


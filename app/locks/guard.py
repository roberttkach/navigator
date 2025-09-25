from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from navigator.core.port.locks import Lock, LockProvider


class ScopeForm(Protocol):
    inline: object | None
    chat: object | None
    business: object | None


def _key(scope: ScopeForm) -> tuple[object | None, object | None]:
    return (
        getattr(scope, "inline", None) or getattr(scope, "chat", None),
        getattr(scope, "business", None),
    )


@dataclass
class _Guard:
    lock: Lock

    async def __aenter__(self) -> None:  # pragma: no cover - thin wrapper
        await self.lock.acquire()

    async def __aexit__(self, exc_type, exc, tb) -> None:  # pragma: no cover - thin wrapper
        releaser = getattr(self.lock, "untether", None)
        if callable(releaser):
            await releaser()
        else:
            self.lock.release()


class Guardian:
    def __init__(self, provider: LockProvider) -> None:
        self._provider = provider

    def __call__(self, scope: ScopeForm) -> _Guard:
        latch = self._provider.latch(_key(scope))
        return _Guard(lock=latch)


__all__ = ["Guardian"]

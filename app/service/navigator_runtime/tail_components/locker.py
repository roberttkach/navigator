"""Guard helpers protecting navigator tail operations."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope


class TailLocker:
    """Provide a scoped guard context for navigator tail operations."""

    def __init__(self, guard: Guardian, scope: Scope) -> None:
        self._guard = guard
        self._scope = scope

    @property
    def scope(self) -> Scope:
        return self._scope

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[Scope]:
        async with self._guard(self._scope):
            yield self._scope


__all__ = ["TailLocker"]

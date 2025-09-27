"""Foundational helpers shared across history operations."""
from __future__ import annotations

from typing import Any, Awaitable, Callable

from navigator.app.locks.guard import Guardian

from ..reporter import NavigatorReporter


class _HistoryOperation:
    """Base helper coordinating guard and telemetry for history actions."""

    def __init__(
        self,
        *,
        guard: Guardian,
        scope,
        reporter: NavigatorReporter,
    ) -> None:
        self._guard = guard
        self._scope = scope
        self._reporter = reporter

    async def _run(
        self,
        method: str,
        action: Callable[[], Awaitable[None]],
        **fields: object,
    ) -> None:
        self._reporter.emit(method, **fields)
        async with self._guard(self._scope):
            await action()


__all__ = ["_HistoryOperation"]

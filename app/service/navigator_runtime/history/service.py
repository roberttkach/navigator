"""Facade aggregating history operations for the runtime."""
from __future__ import annotations

from navigator.core.contracts.back import NavigatorBackContext

from ..bundler import PayloadBundleSource
from .operations import (
    HistoryAddOperation,
    HistoryBackOperation,
    HistoryRebaseOperation,
    HistoryReplaceOperation,
    HistoryTrimOperation,
)


class NavigatorHistoryService:
    """Coordinate history-centric operations via dedicated actions."""

    def __init__(
        self,
        *,
        add: HistoryAddOperation,
        replace: HistoryReplaceOperation,
        rebase: HistoryRebaseOperation,
        back: HistoryBackOperation,
        pop: HistoryTrimOperation,
    ) -> None:
        self._add = add
        self._replace = replace
        self._rebase = rebase
        self._back = back
        self._pop = pop

    async def add(
        self,
        content: PayloadBundleSource,
        *,
        key: str | None = None,
        root: bool = False,
    ) -> None:
        await self._add(content, key=key, root=root)

    async def replace(self, content: PayloadBundleSource) -> None:
        await self._replace(content)

    async def rebase(self, message) -> None:
        await self._rebase(message)

    async def back(self, context: NavigatorBackContext) -> None:
        await self._back(context)

    async def pop(self, count: int = 1) -> None:
        await self._pop(count)


__all__ = ["NavigatorHistoryService"]

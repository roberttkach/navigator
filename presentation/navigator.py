"""Presentation level navigator facade."""
from __future__ import annotations

from typing import Any, SupportsInt

from navigator.app.dto.content import Content, Node
from navigator.app.service import NavigatorRuntime
from navigator.presentation.types import StateLike


class Navigator:
    """Thin wrapper delegating to application level navigator runtime."""

    def __init__(self, runtime: NavigatorRuntime) -> None:
        self._history = runtime.history
        self._state = runtime.state
        self.last = runtime.tail

    async def add(
        self,
        content: Content | Node,
        *,
        key: str | None = None,
        root: bool = False,
    ) -> None:
        await self._history.add(content, key=key, root=root)

    async def replace(self, content: Content | Node) -> None:
        await self._history.replace(content)

    async def rebase(self, message: int | SupportsInt) -> None:
        await self._history.rebase(message)

    async def back(self, context: dict[str, Any]) -> None:
        await self._history.back(context)

    async def set(
        self,
        state: str | StateLike,
        context: dict[str, Any] | None = None,
    ) -> None:
        await self._state.set(state, context)

    async def pop(self, count: int = 1) -> None:
        await self._history.pop(count)

    async def alert(self) -> None:
        await self._state.alert()


__all__ = ["Navigator"]

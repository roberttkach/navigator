"""Generic navigator facade for application runtime consumers."""
from __future__ import annotations

from typing import Any, SupportsInt

from navigator.app.dto.content import Content, Node

from .bundler import bundle_from_dto
from .runtime import NavigatorRuntime
from .tail_components import dto_edit_request
from .types import StateLike


class NavigatorFacade:
    """High-level facade delegating to navigator runtime services."""

    def __init__(self, runtime: NavigatorRuntime) -> None:
        self._history = runtime.history
        self._state = runtime.state
        self._tail = runtime.tail

    async def add(
        self,
        content: Content | Node,
        *,
        key: str | None = None,
        root: bool = False,
    ) -> None:
        await self._history.add(bundle_from_dto(content), key=key, root=root)

    async def replace(self, content: Content | Node) -> None:
        await self._history.replace(bundle_from_dto(content))

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

    async def edit_last(self, content: Content) -> int | None:
        """Edit the last navigator message using DTO ``content``."""

        return await self._tail.edit(dto_edit_request(content))


__all__ = ["NavigatorFacade"]

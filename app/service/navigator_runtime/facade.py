"""Generic navigator facade for application runtime consumers."""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, SupportsInt

from navigator.app.dto.content import Content, Node

from navigator.core.contracts.back import NavigatorBackContext
from .bundler import PayloadBundleSource, bundle_from_dto
from .history import NavigatorHistoryService
from .runtime import NavigatorRuntime
from .state import NavigatorStateService
from .tail import NavigatorTail
from .tail_components import dto_edit_request
from navigator.core.contracts.state import StateLike


@dataclass(frozen=True)
class HistoryContentTranslator:
    """Translate facade DTOs into bundle sources understood by the service."""

    def to_source(self, content: Content | Node) -> PayloadBundleSource:
        return bundle_from_dto(content)


@dataclass(frozen=True)
class NavigatorHistoryFacade:
    """Expose history oriented runtime capabilities."""

    service: NavigatorHistoryService
    translator: HistoryContentTranslator = field(
        default_factory=HistoryContentTranslator
    )

    async def add(
        self,
        content: Content | Node,
        *,
        key: str | None = None,
        root: bool = False,
    ) -> None:
        await self.service.add(
            self.translator.to_source(content),
            key=key,
            root=root,
        )

    async def replace(self, content: Content | Node) -> None:
        await self.service.replace(self.translator.to_source(content))

    async def rebase(self, message: int | SupportsInt) -> None:
        await self.service.rebase(message)

    async def back(self, context: NavigatorBackContext) -> None:
        await self.service.back(context)

    async def pop(self, count: int = 1) -> None:
        await self.service.pop(count)


@dataclass(frozen=True)
class NavigatorStateFacade:
    """Isolate state related runtime capabilities."""

    service: NavigatorStateService

    async def set(
        self,
        state: str | StateLike,
        context: dict[str, Any] | None = None,
    ) -> None:
        await self.service.set(state, context)

    async def alert(self) -> None:
        await self.service.alert()


@dataclass(frozen=True)
class NavigatorTailFacade:
    """Adapt tail-specific runtime behaviour."""

    service: NavigatorTail

    async def edit_last(self, content: Content) -> int | None:
        return await self.service.edit(dto_edit_request(content))


class NavigatorFacade:
    """Aggregate specialised facades for runtime consumers."""

    def __init__(self, runtime: NavigatorRuntime) -> None:
        self.history = NavigatorHistoryFacade(runtime.history)
        self.state = NavigatorStateFacade(runtime.state)
        self.tail = NavigatorTailFacade(runtime.tail)


__all__ = [
    "HistoryContentTranslator",
    "NavigatorFacade",
    "NavigatorHistoryFacade",
    "NavigatorStateFacade",
    "NavigatorTailFacade",
]

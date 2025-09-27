"""Contracts describing navigator assembly inputs and outputs."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Protocol, SupportsInt, runtime_checkable

from navigator.app.service.navigator_runtime.api_contracts import (
    NavigatorAssemblyOverrides,
    NavigatorRuntimeBundleLike,
    NavigatorRuntimeInstrument,
)
from ..core.contracts.back import NavigatorBackContext
from ..core.contracts.state import StateLike


@dataclass(slots=True)
class ScopeDTO:
    """Thin DTO describing chat scope information required by the API."""

    chat: int | None
    lang: str | None = None
    inline: str | None = None
    business: str | None = None
    category: str | None = None
    topic: int | None = None
    direct: bool = False


@runtime_checkable
class ViewLedgerDTO(Protocol):
    """Runtime protocol for dynamic view factories supplied to the API."""

    def get(self, key: str) -> Awaitable[Any] | Any: ...

    def has(self, key: str) -> bool: ...


@runtime_checkable
class NavigatorHistoryLike(Protocol):
    """Protocol describing history oriented facade capabilities."""

    async def add(self, *args: Any, **kwargs: Any) -> Any: ...

    async def replace(self, *args: Any, **kwargs: Any) -> Any: ...

    async def rebase(self, message: int | SupportsInt) -> Any: ...

    async def back(self, context: NavigatorBackContext) -> Any: ...

    async def pop(self, count: int = 1) -> Any: ...


@runtime_checkable
class NavigatorStateLike(Protocol):
    """Protocol describing state oriented facade capabilities."""

    async def set(
        self, state: str | StateLike, context: dict[str, object] | None = None
    ) -> Any: ...

    async def alert(self) -> Any: ...


@runtime_checkable
class NavigatorTailLike(Protocol):
    """Protocol describing tail oriented facade capabilities."""

    async def edit_last(self, content: Any) -> Any: ...


@runtime_checkable
class NavigatorLike(Protocol):
    """Protocol describing the facade returned by :func:`assemble`."""

    history: NavigatorHistoryLike
    state: NavigatorStateLike
    tail: NavigatorTailLike


__all__ = [
    "NavigatorAssemblyOverrides",
    "NavigatorHistoryLike",
    "NavigatorLike",
    "NavigatorRuntimeBundleLike",
    "NavigatorRuntimeInstrument",
    "NavigatorStateLike",
    "NavigatorTailLike",
    "ScopeDTO",
    "ViewLedgerDTO",
]

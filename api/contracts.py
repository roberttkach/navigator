"""Public contracts exposed by the navigator API layer."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Protocol, runtime_checkable


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
class NavigatorLike(Protocol):
    """Protocol describing the facade returned by :func:`assemble`."""

    async def add(self, *args: Any, **kwargs: Any) -> Any: ...


@runtime_checkable
class NavigatorRuntimeBundleLike(Protocol):
    """Structural contract describing runtime bundles exposed to the API."""

    telemetry: Any
    container: Any
    runtime: Any


class NavigatorRuntimeInstrument(Protocol):
    """Protocol describing runtime instrumentation hooks accepted by the API."""

    def __call__(self, bundle: NavigatorRuntimeBundleLike) -> None: ...


__all__ = [
    "NavigatorLike",
    "NavigatorRuntimeBundleLike",
    "NavigatorRuntimeInstrument",
    "ScopeDTO",
    "ViewLedgerDTO",
]

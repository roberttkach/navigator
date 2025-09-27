"""Shared contracts describing runtime assembly collaboration points."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, runtime_checkable


@dataclass(slots=True)
class NavigatorAssemblyOverrides:
    """Configuration overrides accepted by assembly entrypoints."""

    view_container: Any | None = None


@runtime_checkable
class NavigatorRuntimeBundleLike(Protocol):
    """Structural contract describing runtime bundles exposed externally."""

    telemetry: Any
    container: Any
    runtime: Any


class NavigatorRuntimeInstrument(Protocol):
    """Protocol describing runtime instrumentation hooks."""

    def __call__(self, bundle: NavigatorRuntimeBundleLike) -> None: ...


__all__ = [
    "NavigatorAssemblyOverrides",
    "NavigatorRuntimeBundleLike",
    "NavigatorRuntimeInstrument",
]

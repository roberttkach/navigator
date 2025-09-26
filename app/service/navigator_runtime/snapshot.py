"""Snapshot representations for navigator runtime exposure."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.service.navigator_runtime.dependencies import NavigatorDependencies


@dataclass(frozen=True)
class NavigatorRuntimeSnapshot:
    """Immutable view of runtime dependencies exposed by the container."""

    dependencies: NavigatorDependencies
    redaction: str


__all__ = ["NavigatorRuntimeSnapshot"]

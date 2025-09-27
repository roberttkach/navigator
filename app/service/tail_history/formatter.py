"""Formatting helpers for tail history telemetry."""
from __future__ import annotations

from navigator.core.value.message import Scope


class TailHistoryScopeFormatter:
    """Convert scope objects into telemetry-friendly payloads."""

    def describe(self, scope: Scope | None) -> dict[str, object] | None:
        if scope is None:
            return None
        return {
            "chat": getattr(scope, "chat", None),
            "inline": bool(getattr(scope, "inline", None)),
            "business": bool(getattr(scope, "business", None)),
        }


__all__ = ["TailHistoryScopeFormatter"]

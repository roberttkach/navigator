"""Definitions for assembled navigator runtime services."""
from __future__ import annotations

from dataclasses import dataclass

from .history import NavigatorHistoryService
from .state import NavigatorStateService
from .tail import NavigatorTail


@dataclass(frozen=True)
class NavigatorRuntime:
    """Collection of navigator application services."""

    history: NavigatorHistoryService
    state: NavigatorStateService
    tail: NavigatorTail


__all__ = ["NavigatorRuntime"]

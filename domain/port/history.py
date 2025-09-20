from __future__ import annotations

from typing import Protocol, List, runtime_checkable

from ..entity.history import Entry


@runtime_checkable
class HistoryRepository(Protocol):
    """Storage for navigation history."""

    async def get_history(self) -> List[Entry]:
        """Return full history ordered from first to last."""

    async def save_history(self, history: List[Entry]) -> None:
        """Persist full history snapshot."""


__all__ = ["HistoryRepository"]

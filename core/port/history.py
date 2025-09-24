from __future__ import annotations

import typing
from typing import Protocol, List

from ..entity.history import Entry


@typing.runtime_checkable
class HistoryRepository(Protocol):
    """Storage for navigation history."""

    async def recall(self) -> List[Entry]:
        """Return full history ordered from first to last."""

    async def archive(self, history: List[Entry]) -> None:
        """Persist full history snapshot."""


__all__ = ["HistoryRepository"]

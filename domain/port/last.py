from __future__ import annotations

import typing
from typing import Protocol, Optional


@typing.runtime_checkable
class LatestRepository(Protocol):
    """Storage for latest sent message identifier."""

    async def peek(self) -> Optional[int]:
        """Return latest message id or None."""

    async def mark(self, marker: Optional[int]) -> None:
        """Set or clear latest message identifier."""


__all__ = ["LatestRepository"]

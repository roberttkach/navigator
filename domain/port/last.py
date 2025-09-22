from __future__ import annotations

from typing import Protocol, Optional, runtime_checkable


@runtime_checkable
class LastMessageRepository(Protocol):
    """Storage for last sent message identifier."""

    async def peek(self) -> Optional[int]:
        """Return last message id or None."""

    async def mark(self, marker: Optional[int]) -> None:
        """Set or clear last message identifier."""


__all__ = ["LastMessageRepository"]

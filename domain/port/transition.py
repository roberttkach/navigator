from __future__ import annotations

from typing import Protocol, Optional, runtime_checkable


@runtime_checkable
class TransitionObserver(Protocol):
    """Observer for state transitions."""

    async def shift(self, origin: Optional[str], target: str) -> None:
        """React to transition."""


__all__ = ["TransitionObserver"]

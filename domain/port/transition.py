from __future__ import annotations

import typing
from typing import Protocol, Optional


@typing.runtime_checkable
class TransitionObserver(Protocol):
    """Observer for state transitions."""

    async def shift(self, origin: Optional[str], target: str) -> None:
        """React to transition."""


__all__ = ["TransitionObserver"]

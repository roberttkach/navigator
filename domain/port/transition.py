from __future__ import annotations

from typing import Protocol, Optional, runtime_checkable


@runtime_checkable
class TransitionObserver(Protocol):
    """Observer for state transitions."""

    async def on_transition(self, from_state: Optional[str], to_state: str) -> None:
        """React to transition."""


__all__ = ["TransitionObserver"]

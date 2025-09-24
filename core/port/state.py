from __future__ import annotations

import typing
from typing import Protocol, Optional, Dict, Any


@typing.runtime_checkable
class StateRepository(Protocol):
    """FSM state storage."""

    async def status(self) -> Optional[str]:
        """Return current state or None."""

    async def assign(self, state: Optional[str]) -> None:
        """Set current state."""

    async def payload(self) -> Dict[str, Any]:
        """Return FSM data payload."""


__all__ = ["StateRepository"]

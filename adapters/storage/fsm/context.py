"""Protocols describing the requirements for FSM storage backends."""
from __future__ import annotations

from typing import Any, Dict, Optional, Protocol, runtime_checkable


@runtime_checkable
class StateContext(Protocol):
    """Minimal asynchronous interface expected from FSM backends."""

    async def get_state(self) -> Optional[str]:
        """Return current state identifier."""

    async def set_state(self, state: Optional[str]) -> None:
        """Persist a new state identifier."""

    async def get_data(self) -> Dict[str, Any]:
        """Return arbitrary payload stored for the state machine."""

    async def update_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Merge ``data`` into the stored payload and return the result."""


__all__ = ["StateContext"]

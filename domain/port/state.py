from __future__ import annotations

from typing import Protocol, Optional, Dict, Any, runtime_checkable

from ..entity.stategraph import Graph


@runtime_checkable
class StateRepository(Protocol):
    """FSM state and graph storage."""

    async def get_state(self) -> Optional[str]:
        """Return current state or None."""

    async def set_state(self, state: Optional[str]) -> None:
        """Set current state."""

    async def get_graph(self) -> Graph:
        """Return state graph."""

    async def save_graph(self, graph: Graph) -> None:
        """Persist state graph."""

    async def get_data(self) -> Dict[str, Any]:
        """Return FSM data payload."""


__all__ = ["StateRepository"]

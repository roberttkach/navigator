from __future__ import annotations

import typing
from typing import Protocol, Optional, Dict, Any

from ..entity.graph import Graph


@typing.runtime_checkable
class StateRepository(Protocol):
    """FSM state and graph storage."""

    async def status(self) -> Optional[str]:
        """Return current state or None."""

    async def assign(self, state: Optional[str]) -> None:
        """Set current state."""

    async def diagram(self) -> Graph:
        """Return state graph."""

    async def capture(self, graph: Graph) -> None:
        """Persist state graph."""

    async def payload(self) -> Dict[str, Any]:
        """Return FSM data payload."""


__all__ = ["StateRepository"]

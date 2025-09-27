"""Rendering helpers delegated by the add use case."""

from __future__ import annotations

from typing import Optional, Sequence

from ...core.entity.history import Entry
from ...core.value.content import Payload
from ...core.value.message import Scope
from ...service.view.planner import ViewPlanner


class AppendRenderPlanner:
    """Delegate render planning to the configured view planner."""

    def __init__(self, planner: ViewPlanner) -> None:
        self._planner = planner

    async def plan(
            self,
            scope: Scope,
            payloads: Sequence[Payload],
            trail: Optional[Entry],
    ) -> object:
        return await self._planner.render(
            scope,
            payloads,
            trail,
            inline=bool(scope.inline),
        )


__all__ = ["AppendRenderPlanner"]


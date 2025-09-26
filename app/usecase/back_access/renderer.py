"""View rendering helpers for rewind workflows."""
from __future__ import annotations

from typing import Any

from navigator.app.service.view.planner import ViewPlanner
from navigator.app.service.view.restorer import ViewRestorer
from navigator.core.entity.history import Entry
from navigator.core.value.message import Scope


class RewindRenderer:
    """Handle payload revive and render planning for rewind."""

    def __init__(
        self,
        restorer: ViewRestorer,
        planner: ViewPlanner,
    ) -> None:
        self._restorer = restorer
        self._planner = planner

    async def revive(
        self,
        target: Entry,
        context: dict[str, Any],
        memory: dict[str, Any],
        *,
        inline: bool,
    ) -> list[Any]:
        merged = {**memory, **context}
        revived = await self._restorer.revive(target, merged, inline=inline)
        return [*revived]

    async def render(
        self,
        scope: Scope,
        payloads: list[Any],
        origin: Entry,
        *,
        inline: bool,
    ) -> object:
        return await self._planner.render(
            scope,
            payloads,
            origin,
            inline=inline,
        )

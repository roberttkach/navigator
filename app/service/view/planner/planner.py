"""Plan edits, deletions, and sends for a desired payload state."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Optional

from navigator.core.entity.history import Entry
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .inline import InlineRenderPlanner
from .models import RenderNode, RenderState
from .preparer import RenderPreparer
from .regular import RegularRenderPlanner


class ViewPlanner:
    """Plan edits, deletions, and sends for a desired payload state."""

    def __init__(
        self,
        inline: InlineRenderPlanner,
        regular: RegularRenderPlanner,
        preparer: RenderPreparer,
    ) -> None:
        self._inline_planner = inline
        self._regular_planner = regular
        self._prepare = preparer

    async def render(
        self,
        scope: Scope,
        payloads: Sequence[Payload],
        trail: Optional[Entry],
        *,
        inline: bool,
    ) -> Optional[RenderNode]:
        """Plan rendering actions for ``payloads`` within ``scope``."""

        fresh = self._prepare.prepare(scope, payloads, inline=inline)
        ledger = list(trail.messages) if trail else []

        state = RenderState()
        if inline:
            mutated = await self._inline_planner.plan(scope, fresh, ledger, state)
        else:
            mutated = await self._regular_planner.plan(scope, fresh, ledger, state)

        if not state.ids:
            return None

        return RenderNode(ids=state.ids, extras=state.extras, metas=state.metas, changed=mutated)


__all__ = ["ViewPlanner"]


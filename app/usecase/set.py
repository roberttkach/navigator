"""Coordinate state restoration to reconcile history with a desired goal."""

from __future__ import annotations

from typing import Any, Dict, Optional

from ..log import events
from ..log.aspect import TraceAspect
from ..service.view.planner import RenderNode, ViewPlanner
from ...core.entity.history import Entry
from ...core.value.content import Payload
from ...core.telemetry import Telemetry
from ...core.value.message import Scope
from .set_components import (
    HistoryReconciler,
    HistoryRestorationPlanner,
    PayloadReviver,
    RestorationPlan,
    StateSynchronizer,
)


class Setter:
    """Restore and re-render history entries to satisfy a ``goal`` state."""

    def __init__(
            self,
            planner: HistoryRestorationPlanner,
            state: StateSynchronizer,
            reviver: PayloadReviver,
            renderer: ViewPlanner,
            reconciler: HistoryReconciler,
            telemetry: Telemetry,
    ):
        self._planner = planner
        self._state = state
        self._reviver = reviver
        self._renderer = renderer
        self._reconciler = reconciler
        self._trace = TraceAspect(telemetry)

    async def execute(
            self,
            scope: Scope,
            goal: str,
            context: Dict[str, Any],
    ) -> None:
        """Restore ``goal`` entry for ``scope`` using additional ``context``."""

        await self._trace.run(events.SET, self._perform, scope, goal, context)

    async def _perform(
            self,
            scope: Scope,
            goal: str,
            context: Dict[str, Any],
    ) -> None:
        """Run the state restoration workflow for ``goal``."""

        plan = await self._planner.build(scope, goal)
        await self._reconciler.truncate(plan)
        await self._state.assign(plan.target)
        resolved = await self._reviver.revive(plan.target, context, inline=plan.inline)
        render = await self._render(scope, resolved, plan.tail, plan.inline)
        if render and render.changed:
            await self._reconciler.apply(scope, render)
        else:
            await self._reconciler.skip()

    async def _render(
            self,
            scope: Scope,
            resolved: list[Payload],
            tail: Entry,
            inline: bool,
    ) -> Optional[RenderNode]:
        """Render ``resolved`` payloads against ``tail`` context."""

        return await self._renderer.render(
            scope,
            resolved,
            tail,
            inline=inline,
        )

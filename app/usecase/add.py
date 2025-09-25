"""Coordinate history append operations with view updates."""

from __future__ import annotations

import logging
from typing import List, Optional

from ..log import events
from ..log.aspect import TraceAspect
from ..map.entry import EntryMapper
from ..service.view.planner import ViewPlanner
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import Payload
from ...core.value.message import Scope
from .add_components import AppendHistoryAccess, AppendHistoryWriter, AppendPreparation


class Appender:
    """Manage append operations against conversation history."""

    def __init__(
            self,
            archive,
            state,
            tail,
            planner: ViewPlanner,
            mapper: EntryMapper,
            limit: int,
            telemetry: Telemetry,
            history: AppendHistoryAccess | None = None,
            preparation: AppendPreparation | None = None,
            writer: AppendHistoryWriter | None = None,
    ):
        self._history = history or AppendHistoryAccess(archive, state, telemetry)
        self._prepare = preparation or AppendPreparation(planner, mapper)
        self._writer = writer or AppendHistoryWriter(archive, tail, limit, telemetry)
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._trace = TraceAspect(telemetry)

    async def execute(
            self,
            scope: Scope,
            bundle: List[Payload],
            view: Optional[str],
            root: bool = False,
    ) -> None:
        """Append ``bundle`` to ``scope`` while respecting ``view`` hints."""

        await self._trace.run(
            events.APPEND,
            self._perform,
            scope,
            bundle,
            view,
            root=root,
        )

    async def _perform(
            self,
            scope: Scope,
            bundle: List[Payload],
            view: Optional[str],
            *,
            root: bool = False,
    ) -> None:
        adjusted = self._prepare.normalize(scope, bundle)
        records = await self._history.snapshot(scope)
        trail = records[-1] if records else None
        render = await self._prepare.plan(scope, adjusted, trail)
        if not render or not render.ids or not render.changed:
            self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="add")
            return
        status = await self._history.status()

        entry = self._prepare.entry(adjusted, render, status, view, root)
        timeline = self._prepare.timeline(records, entry, root)
        await self._writer.persist(timeline)

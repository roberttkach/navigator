from __future__ import annotations

import logging
from typing import List, Optional

from ..log import events
from ..log.aspect import TraceAspect
from ..map.entry import EntryMapper, Outcome
from ..service.view.planner import ViewPlanner
from ..service.view.policy import adapt
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from ...core.port.state import StateRepository
from ...core.service.history.policy import prune as prune_history
from ...core.service.scope import profile
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import Payload, normalize
from ...core.value.message import Scope


class Appender:
    def __init__(
            self,
            archive: HistoryRepository,
            state: StateRepository,
            tail: LatestRepository,
            planner: ViewPlanner,
            mapper: EntryMapper,
            limit: int,
            telemetry: Telemetry,
    ):
        self._archive = archive
        self._state = state
        self._tail = tail
        self._planner = planner
        self._mapper = mapper
        self._limit = limit
        self._telemetry = telemetry
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._trace = TraceAspect(telemetry)

    async def execute(
            self,
            scope: Scope,
            bundle: List[Payload],
            view: Optional[str],
            root: bool = False,
    ) -> None:
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
        adjusted = [adapt(scope, normalize(p)) for p in bundle]
        records = await self._archive.recall()
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="add",
            history={"len": len(records)},
            scope=profile(scope),
        )

        trail = records[-1] if records else None
        render = await self._planner.render(
            scope,
            adjusted,
            trail,
            inline=bool(scope.inline),
        )
        if not render or not render.ids or not render.changed:
            self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="add")
            return
        status = await self._state.status()
        self._channel.emit(
            logging.INFO,
            LogCode.STATE_GET,
            op="add",
            state={"current": status},
        )

        usable = adjusted[:len(render.ids)]
        entry = self._mapper.convert(
            Outcome(render.ids, render.extras, render.metas),
            usable,
            status,
            view,
            root,
            base=None,
        )

        timeline = [entry] if root else (records + [entry])
        from ..service.store import persist
        await persist(
            self._archive,
            self._tail,
            prune_history,
            self._limit,
            timeline,
            operation="add",
            telemetry=self._telemetry,
        )

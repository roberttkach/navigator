"""Coordinate history append operations with view updates."""

from __future__ import annotations

import logging
from typing import List, Optional

from ..log import events
from ..log.aspect import TraceAspect
from ..map.entry import EntryMapper, Outcome
from ..service.store import persist
from ..service.view.planner import ViewPlanner
from ..service.view.policy import adapt
from ...core.entity.history import Entry
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from ...core.port.state import StateRepository
from ...core.service.history.policy import prune as prune_history
from ...core.service.scope import profile
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import Payload, normalize
from ...core.value.message import Scope


class Appender:
    """Manage append operations against conversation history."""

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
        adjusted = self._normalize_bundle(scope, bundle)
        records = await self._load_history(scope)
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

        entry = self._build_entry(adjusted, render, status, view, root)
        timeline = self._timeline(records, entry, root)
        await self._persist(timeline)

    def _normalize_bundle(self, scope: Scope, bundle: List[Payload]) -> List[Payload]:
        """Return payloads adapted to ``scope`` rendering expectations."""

        return [adapt(scope, normalize(payload)) for payload in bundle]

    async def _load_history(self, scope: Scope) -> List[Entry]:
        """Load current history snapshot and report telemetry."""

        records = await self._archive.recall()
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="add",
            history={"len": len(records)},
            scope=profile(scope),
        )
        return records

    def _build_entry(
            self,
            adjusted: List[Payload],
            render: object,
            state: Optional[str],
            view: Optional[str],
            root: bool,
    ) -> Entry:
        """Convert render outcome and payloads into a history entry."""

        identifiers = getattr(render, "ids", None) or []
        usable = adjusted[:len(identifiers)]
        outcome = Outcome(
            identifiers,
            getattr(render, "extras", None),
            getattr(render, "metas", []),
        )
        return self._mapper.convert(
            outcome,
            usable,
            state,
            view,
            root,
            base=None,
        )

    def _timeline(self, records: List[Entry], entry: Entry, root: bool) -> List[Entry]:
        """Return a timeline that incorporates ``entry`` respecting ``root``."""

        if root:
            return [entry]
        return [*records, entry]

    async def _persist(self, timeline: List[Entry]) -> None:
        """Persist ``timeline`` and refresh latest message marker."""

        await persist(
            self._archive,
            self._tail,
            prune_history,
            self._limit,
            timeline,
            operation="add",
            telemetry=self._telemetry,
        )

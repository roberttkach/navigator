"""Replace the latest history entry with freshly rendered payloads."""

from __future__ import annotations

import logging
from typing import List

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
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import Payload, normalize
from ...core.value.message import Scope


class Swapper:
    """Replace the trailing history entry with a newly mapped version."""

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

    async def execute(self, scope: Scope, bundle: List[Payload]) -> None:
        """Replace history entry within ``scope`` using ``bundle`` payloads."""

        await self._trace.run(events.REPLACE, self._perform, scope, bundle)

    async def _perform(self, scope: Scope, bundle: List[Payload]) -> None:
        adjusted = self._normalize_bundle(scope, bundle)
        records = await self._load_history()
        trail = records[-1] if records else None
        render = await self._planner.render(
            scope,
            adjusted,
            trail,
            inline=bool(scope.inline),
        )

        if not render or not render.ids or not render.changed:
            self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="replace")
            return
        status = await self._state.status()

        entry = self._build_entry(trail, adjusted, render, status)
        timeline = self._timeline(records, entry)
        await self._persist(timeline)

    def _normalize_bundle(self, scope: Scope, bundle: List[Payload]) -> List[Payload]:
        """Return payloads adapted to ``scope`` expectations."""

        return [adapt(scope, normalize(payload)) for payload in bundle]

    async def _load_history(self) -> List[Entry]:
        """Load current history records and report telemetry."""

        records = await self._archive.recall()
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="replace",
            history={"len": len(records)},
        )
        return records

    def _build_entry(
            self,
            trail: Entry | None,
            adjusted: List[Payload],
            render: object,
            state: str | None,
    ) -> Entry:
        """Map ``render`` outcome to a persisted history entry."""

        identifiers = getattr(render, "ids", None) or []
        usable = adjusted[:len(identifiers)]
        outcome = Outcome(
            identifiers,
            getattr(render, "extras", None),
            getattr(render, "metas", []),
        )
        view = trail.view if trail else None
        root = bool(trail.root) if trail else False
        return self._mapper.convert(
            outcome,
            usable,
            state,
            view,
            root,
            base=trail,
        )

    def _timeline(self, records: List[Entry], entry: Entry) -> List[Entry]:
        """Return a history timeline with ``entry`` as the newest snapshot."""

        if not records:
            return [entry]
        return [*records[:-1], entry]

    async def _persist(self, timeline: List[Entry]) -> None:
        """Persist ``timeline`` updates and latest marker."""

        await persist(
            self._archive,
            self._tail,
            prune_history,
            self._limit,
            timeline,
            operation="replace",
            telemetry=self._telemetry,
        )

"""Supporting collaborators for the ``add`` use case."""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence

from navigator.app.map.entry import EntryMapper, Outcome
from navigator.app.service.view.planner import ViewPlanner
from navigator.app.service.view.policy import adapt
from navigator.app.service.store import persist
from navigator.core.entity.history import Entry
from navigator.core.port.history import HistoryRepository
from navigator.core.port.last import LatestRepository
from navigator.core.port.state import StateRepository
from navigator.core.service.history.policy import prune as prune_history
from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.content import Payload, normalize
from navigator.core.value.message import Scope


class AppendHistoryAccess:
    """Provide read/write helpers around history repositories."""

    def __init__(
            self,
            archive: HistoryRepository,
            state: StateRepository,
            tail: LatestRepository,
            limit: int,
            telemetry: Telemetry,
    ) -> None:
        self._archive = archive
        self._state = state
        self._tail = tail
        self._limit = limit
        self._telemetry = telemetry
        self._channel: TelemetryChannel = telemetry.channel(
            f"{__name__}.history"
        )

    async def snapshot(self, scope: Scope) -> List[Entry]:
        records = await self._archive.recall()
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="add",
            history={"len": len(records)},
            scope=profile(scope),
        )
        return records

    async def status(self) -> Optional[str]:
        status = await self._state.status()
        self._channel.emit(
            logging.INFO,
            LogCode.STATE_GET,
            op="add",
            state={"current": status},
        )
        return status

    async def persist(self, timeline: Sequence[Entry]) -> None:
        await persist(
            self._archive,
            self._tail,
            prune_history,
            self._limit,
            list(timeline),
            operation="add",
            telemetry=self._telemetry,
        )


class AppendPreparation:
    """Prepare payloads and entries for history persistence."""

    def __init__(self, planner: ViewPlanner, mapper: EntryMapper) -> None:
        self._planner = planner
        self._mapper = mapper

    def normalize(self, scope: Scope, bundle: List[Payload]) -> List[Payload]:
        return [adapt(scope, normalize(payload)) for payload in bundle]

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

    def entry(
            self,
            adjusted: List[Payload],
            render: object,
            state: Optional[str],
            view: Optional[str],
            root: bool,
    ) -> Entry:
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

    @staticmethod
    def timeline(records: List[Entry], entry: Entry, root: bool) -> List[Entry]:
        if root:
            return [entry]
        return [*records, entry]


__all__ = [
    "AppendHistoryAccess",
    "AppendPreparation",
]

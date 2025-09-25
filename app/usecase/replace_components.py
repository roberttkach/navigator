"""Support collaborators for the ``replace`` use case."""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence

from navigator.app.map.entry import EntryMapper, Outcome
from navigator.app.service.store import HistoryPersistencePipeline
from navigator.app.service.view.planner import ViewPlanner
from navigator.app.service.view.policy import adapt
from navigator.core.entity.history import Entry
from navigator.core.port.history import HistoryRepository
from navigator.core.port.last import LatestRepository
from navigator.core.port.state import StateRepository
from navigator.core.service.history.policy import prune as prune_history
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.content import Payload, normalize
from navigator.core.value.message import Scope


class ReplaceHistoryAccess:
    """Provide history and state access for replace operations."""

    def __init__(
            self,
            archive: HistoryRepository,
            state: StateRepository,
            telemetry: Telemetry,
    ) -> None:
        self._archive = archive
        self._state = state
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.history")

    async def snapshot(self) -> List[Entry]:
        """Load the current history snapshot with telemetry reporting."""

        records = await self._archive.recall()
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="replace",
            history={"len": len(records)},
        )
        return records

    async def status(self) -> Optional[str]:
        """Return the persisted conversation state."""

        return await self._state.status()


class ReplacePreparation:
    """Prepare payload bundles and entries for history replacement."""

    def __init__(self, planner: ViewPlanner, mapper: EntryMapper) -> None:
        self._planner = planner
        self._mapper = mapper

    def normalize(self, scope: Scope, bundle: Sequence[Payload]) -> List[Payload]:
        """Normalize incoming payloads against ``scope`` expectations."""

        return [adapt(scope, normalize(payload)) for payload in bundle]

    async def plan(
            self,
            scope: Scope,
            payloads: Sequence[Payload],
            trail: Entry | None,
    ) -> object:
        """Plan rendering operations for ``payloads`` within ``scope``."""

        return await self._planner.render(
            scope,
            payloads,
            trail,
            inline=bool(scope.inline),
        )

    def entry(
            self,
            trail: Entry | None,
            adjusted: List[Payload],
            render: object,
            state: Optional[str],
    ) -> Entry:
        """Convert ``render`` outcome to a persisted history entry."""

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

    @staticmethod
    def timeline(records: List[Entry], entry: Entry) -> List[Entry]:
        """Return a new timeline with ``entry`` replacing the latest snapshot."""

        if not records:
            return [entry]
        return [*records[:-1], entry]


class ReplaceHistoryWriter:
    """Persist replace outcomes using the history persistence pipeline."""

    def __init__(
            self,
            archive: HistoryRepository,
            tail: LatestRepository,
            limit: int,
            telemetry: Telemetry,
            *,
            pipeline: HistoryPersistencePipeline | None = None,
    ) -> None:
        self._pipeline = pipeline or HistoryPersistencePipeline(
            archive=archive,
            ledger=tail,
            prune_history=prune_history,
            limit=limit,
            telemetry=telemetry,
        )

    async def persist(self, timeline: Sequence[Entry]) -> None:
        """Persist ``timeline`` updates with replace telemetry."""

        await self._pipeline.persist(timeline, operation="replace")


__all__ = [
    "ReplaceHistoryAccess",
    "ReplacePreparation",
    "ReplaceHistoryWriter",
]


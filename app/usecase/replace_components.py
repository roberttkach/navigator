"""Support collaborators for the ``replace`` use case."""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence, Protocol

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
from .render_contract import RenderOutcome


class ReplaceHistoryObserver(Protocol):
    """Side effects performed when accessing replace history collaborators."""

    def history_loaded(self, count: int) -> None: ...

    def state_retrieved(self, status: Optional[str]) -> None: ...


class NullReplaceHistoryObserver(ReplaceHistoryObserver):
    """No-op observer shielding history access from optional telemetry."""

    def history_loaded(self, count: int) -> None:  # pragma: no cover - intentional noop
        return

    def state_retrieved(self, status: Optional[str]) -> None:  # pragma: no cover - intentional noop
        return


class ReplaceHistoryJournal(ReplaceHistoryObserver):
    """Emit telemetry events for history loads and status retrievals."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.history")

    def history_loaded(self, count: int) -> None:
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="replace",
            history={"len": count},
        )

    def state_retrieved(self, status: Optional[str]) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.STATE_GET,
            op="replace",
            state={"current": status},
        )


class ReplaceHistoryAccess:
    """Provide history and state access for replace operations."""

    def __init__(
            self,
            archive: HistoryRepository,
            state: StateRepository,
            observer: ReplaceHistoryObserver | None = None,
    ) -> None:
        self._archive = archive
        self._state = state
        self._observer: ReplaceHistoryObserver = observer or NullReplaceHistoryObserver()

    async def snapshot(self) -> List[Entry]:
        """Load the current history snapshot with telemetry reporting."""

        records = await self._archive.recall()
        self._observer.history_loaded(len(records))
        return records

    async def status(self) -> Optional[str]:
        """Return the persisted conversation state."""

        status = await self._state.status()
        self._observer.state_retrieved(status)
        return status


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
    ) -> RenderOutcome | None:
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
            render: RenderOutcome,
            state: Optional[str],
    ) -> Entry:
        """Convert ``render`` outcome to a persisted history entry."""

        identifiers = list(render.ids)
        usable = adjusted[:len(identifiers)]
        outcome = Outcome(identifiers, list(render.extras), list(render.metas))
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
    "NullReplaceHistoryObserver",
    "ReplaceHistoryJournal",
    "ReplaceHistoryObserver",
]


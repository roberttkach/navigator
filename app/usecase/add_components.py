"""Supporting collaborators for the ``add`` use case."""

from __future__ import annotations

import logging
from typing import List, Optional, Sequence, Protocol

from navigator.app.map.entry import EntryMapper, Outcome
from navigator.app.service.view.planner import ViewPlanner
from navigator.app.service.view.policy import adapt
from navigator.app.service.store import (
    HistoryPersistencePipeline,
    HistoryPersistencePipelineFactory,
)
from navigator.core.entity.history import Entry
from navigator.core.port.history import HistoryRepository
from navigator.core.port.state import StateRepository
from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.content import Payload, normalize
from navigator.core.value.message import Scope
from .render_contract import RenderOutcome


class AppendHistoryObserver(Protocol):
    """Protocol describing side effects performed during append access."""

    def history_loaded(self, scope: Scope, count: int) -> None: ...

    def state_retrieved(self, status: Optional[str]) -> None: ...


class NullAppendHistoryObserver:
    """No-op implementation shielding access from optional observers."""

    def history_loaded(self, scope: Scope, count: int) -> None:  # pragma: no cover - no-op
        return

    def state_retrieved(self, status: Optional[str]) -> None:  # pragma: no cover - no-op
        return


class AppendHistoryJournal(AppendHistoryObserver):
    """Emit telemetry envelopes for append history events."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.history")

    def history_loaded(self, scope: Scope, count: int) -> None:
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="add",
            history={"len": count},
            scope=profile(scope),
        )

    def state_retrieved(self, status: Optional[str]) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.STATE_GET,
            op="add",
            state={"current": status},
        )


class HistorySnapshotAccess:
    """Expose history snapshots while notifying interested observers."""

    def __init__(
            self,
            archive: HistoryRepository,
            observer: AppendHistoryObserver | None = None,
    ) -> None:
        self._archive = archive
        self._observer: AppendHistoryObserver = observer or NullAppendHistoryObserver()

    async def snapshot(self, scope: Scope) -> List[Entry]:
        records = await self._archive.recall()
        self._observer.history_loaded(scope, len(records))
        return records


class StateStatusAccess:
    """Retrieve state information while surfacing observer notifications."""

    def __init__(
            self,
            state: StateRepository,
            observer: AppendHistoryObserver | None = None,
    ) -> None:
        self._state = state
        self._observer: AppendHistoryObserver = observer or NullAppendHistoryObserver()

    async def status(self) -> Optional[str]:
        status = await self._state.status()
        self._observer.state_retrieved(status)
        return status


class AppendHistoryWriter:
    """Persist history timelines while applying pruning policy."""

    def __init__(
            self,
            pipeline_factory: HistoryPersistencePipelineFactory,
            *,
            pipeline: HistoryPersistencePipeline | None = None,
    ) -> None:
        self._pipeline_factory = pipeline_factory
        self._pipeline = pipeline

    def _resolve_pipeline(self) -> HistoryPersistencePipeline:
        if self._pipeline is None:
            self._pipeline = self._pipeline_factory.create()
        return self._pipeline

    async def persist(self, timeline: Sequence[Entry]) -> None:
        pipeline = self._resolve_pipeline()
        await pipeline.persist(list(timeline), operation="add")


class AppendPayloadAdapter:
    """Apply normalisation and scope-specific adjustments to payload bundles."""

    def normalize(self, scope: Scope, bundle: List[Payload]) -> List[Payload]:
        return [adapt(scope, normalize(payload)) for payload in bundle]


class AppendRenderPlanner:
    """Delegate render planning to the configured view planner."""

    def __init__(self, planner: ViewPlanner) -> None:
        self._planner = planner

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


class AppendEntryAssembler:
    """Build entries and timelines using render outcomes."""

    def __init__(self, mapper: EntryMapper) -> None:
        self._mapper = mapper

    def build_entry(
            self,
            adjusted: List[Payload],
            render: RenderOutcome,
            state: Optional[str],
            view: Optional[str],
            root: bool,
            *,
            base: Optional[Entry] = None,
    ) -> Entry:
        identifiers = list(render.ids)
        usable = adjusted[:len(identifiers)]
        outcome = Outcome(identifiers, list(render.extras), list(render.metas))
        return self._mapper.convert(
            outcome,
            usable,
            state,
            view,
            root,
            base=base,
        )

    @staticmethod
    def extend_timeline(records: List[Entry], entry: Entry, root: bool) -> List[Entry]:
        if root:
            return [entry]
        return [*records, entry]


__all__ = [
    "AppendEntryAssembler",
    "AppendHistoryObserver",
    "AppendHistoryJournal",
    "AppendHistoryWriter",
    "AppendPayloadAdapter",
    "AppendRenderPlanner",
    "HistorySnapshotAccess",
    "NullAppendHistoryObserver",
    "StateStatusAccess",
]

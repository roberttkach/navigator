"""History access and persistence helpers for the add use case."""

from __future__ import annotations

from typing import List, Optional, Sequence

from navigator.core.entity.history import Entry
from navigator.core.port.history import HistoryRepository
from navigator.core.port.state import StateRepository
from navigator.core.value.message import Scope

from .observer import AppendHistoryObserver, NullAppendHistoryObserver
from ...service.store import (
    HistoryPersistencePipeline,
    HistoryPersistencePipelineFactory,
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


__all__ = [
    "AppendHistoryWriter",
    "HistorySnapshotAccess",
    "StateStatusAccess",
]


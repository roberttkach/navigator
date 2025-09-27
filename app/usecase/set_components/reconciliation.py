"""Reconciliation helpers coordinating tail updates and telemetry."""
from __future__ import annotations

import logging
from dataclasses import dataclass

from navigator.core.port.history import HistoryRepository
from navigator.core.port.last import LatestRepository
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope

from ..render_contract import RenderOutcome
from .planning import RestorationPlan
from .tail import HistoryTailWriter


class TailMarkerAccess:
    """Persist last marker updates produced during reconciliation."""

    def __init__(self, latest: LatestRepository) -> None:
        self._latest = latest

    async def mark(self, marker: int) -> None:
        await self._latest.mark(marker)


class ReconciliationJournal:
    """Emit telemetry events describing reconciliation lifecycle."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.reconcile")

    def record_mark(self, marker: int) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.LAST_SET,
            op="set",
            message={"id": marker},
        )

    def record_skip(self) -> None:
        self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="set")


@dataclass(slots=True)
class HistoryReconciler:
    """Coordinate reconciliation between history, markers and telemetry."""

    writer: HistoryTailWriter
    marker: TailMarkerAccess
    journal: ReconciliationJournal

    @classmethod
    def from_components(
        cls,
        ledger: HistoryRepository,
        latest: LatestRepository,
        telemetry: Telemetry,
    ) -> "HistoryReconciler":
        writer = HistoryTailWriter(ledger)
        marker = TailMarkerAccess(latest)
        journal = ReconciliationJournal(telemetry)
        return cls(writer, marker, journal)

    async def truncate(self, plan: RestorationPlan) -> None:
        await self.writer.truncate(plan)

    async def apply(self, _scope: Scope, render: RenderOutcome) -> None:
        await self.writer.apply(render)
        await self.marker.mark(render.ids[0])
        self.journal.record_mark(render.ids[0])

    async def skip(self) -> None:
        self.journal.record_skip()


__all__ = [
    "HistoryReconciler",
    "ReconciliationJournal",
    "TailMarkerAccess",
]

"""History writing helpers supporting rewind workflows."""
from __future__ import annotations

from collections.abc import Sequence

from navigator.core.entity.history import Entry
from navigator.core.port.history import HistoryRepository
from navigator.core.port.last import LatestRepository
from navigator.core.port.state import StateRepository

from .telemetry import RewindWriteTelemetry


class RewindHistoryWriter:
    """Persist rewind side-effects while emitting telemetry."""

    def __init__(
        self,
        ledger: HistoryRepository,
        status: StateRepository,
        latest: LatestRepository,
        instrumentation: RewindWriteTelemetry,
    ) -> None:
        self._ledger = ledger
        self._status = status
        self._latest = latest
        self._instrumentation = instrumentation

    async def assign_state(self, state: str | None) -> None:
        """Persist ``state`` and report bookkeeping telemetry."""

        if state is None:
            return
        await self._status.assign(state)
        self._instrumentation.state_assigned(state)

    async def mark_latest(self, identifier: int | None) -> None:
        """Mark ``identifier`` as the latest message when provided."""

        if identifier is None:
            return
        await self._latest.mark(identifier)
        self._instrumentation.latest_marked(identifier)

    async def archive(self, history: Sequence[Entry]) -> None:
        """Persist ``history`` snapshot with telemetry."""

        snapshot = list(history)
        await self._ledger.archive(snapshot)
        self._instrumentation.history_saved(len(snapshot))

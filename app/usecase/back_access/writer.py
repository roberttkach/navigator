"""Write-side helpers supporting rewind flows."""

from __future__ import annotations

from collections.abc import Sequence

from navigator.core.entity.history import Entry
from navigator.core.port.history import HistoryRepository
from navigator.core.port.last import LatestRepository
from navigator.core.port.state import StateRepository

from .telemetry import RewindWriteTelemetry


class RewindHistoryArchiver:
    """Persist history snapshots while reporting telemetry."""

    def __init__(
        self, ledger: HistoryRepository, instrumentation: RewindWriteTelemetry
    ) -> None:
        self._ledger = ledger
        self._instrumentation = instrumentation

    async def archive(self, history: Sequence[Entry]) -> list[Entry]:
        """Persist ``history`` snapshot and return stored copy."""

        snapshot = list(history)
        await self._ledger.archive(snapshot)
        self._instrumentation.history_saved(len(snapshot))
        return snapshot


class RewindStateWriter:
    """Persist FSM state updates produced by rewind."""

    def __init__(
        self, status: StateRepository, instrumentation: RewindWriteTelemetry
    ) -> None:
        self._status = status
        self._instrumentation = instrumentation

    async def assign(self, state: str | None) -> None:
        """Persist ``state`` when provided."""

        if state is None:
            return
        await self._status.assign(state)
        self._instrumentation.state_assigned(state)


class RewindLatestMarker:
    """Update latest message markers with telemetry."""

    def __init__(
        self, latest: LatestRepository, instrumentation: RewindWriteTelemetry
    ) -> None:
        self._latest = latest
        self._instrumentation = instrumentation

    async def mark(self, identifier: int | None) -> None:
        """Mark ``identifier`` when available."""

        if identifier is None:
            return
        await self._latest.mark(identifier)
        self._instrumentation.latest_marked(identifier)


__all__ = [
    "RewindHistoryArchiver",
    "RewindLatestMarker",
    "RewindStateWriter",
]

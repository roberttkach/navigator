"""History persistence pipeline components."""
from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import dataclass

from ....core.entity.history import Entry
from ....core.port.history import HistoryRepository
from ....core.port.last import LatestRepository
from ....core.telemetry import LogCode, Telemetry, TelemetryChannel


def _latest_marker(history: Sequence[Entry]) -> int | None:
    """Return the first message identifier for the most recent entry."""

    if not history:
        return None
    messages = history[-1].messages
    if not messages:
        return None
    return messages[0].id


class HistoryTelemetryReporter:
    """Emit telemetry envelopes describing persistence operations."""

    def __init__(self, telemetry: Telemetry | None) -> None:
        self._channel: TelemetryChannel | None = (
            telemetry.channel(__name__) if telemetry else None
        )

    def trimmed(self, *, operation: str, before: int, after: int) -> None:
        """Report history trimming when the snapshot was reduced."""

        if self._channel is None or before == after:
            return
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_TRIM,
            op=operation,
            history={"before": before, "after": after},
        )

    def saved(self, *, operation: str, size: int) -> None:
        """Report snapshot archiving."""

        if self._channel is None:
            return
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op=operation,
            history={"len": size},
        )

    def marker_updated(self, *, operation: str, message_id: int) -> None:
        """Report updates to the latest message marker."""

        if self._channel is None:
            return
        self._channel.emit(
            logging.INFO,
            LogCode.LAST_SET,
            op=operation,
            message={"id": message_id},
        )


class HistoryTrimmer:
    """Trim history snapshots according to the configured policy."""

    def __init__(
        self,
        policy: Callable[[list[Entry], int], list[Entry]],
        limit: int,
        reporter: HistoryTelemetryReporter,
    ) -> None:
        self._policy = policy
        self._limit = limit
        self._reporter = reporter

    def apply(self, history: Sequence[Entry], *, operation: str) -> list[Entry]:
        """Return trimmed history while emitting telemetry when truncation occurs."""

        snapshot = list(history)
        trimmed = self._policy(snapshot, self._limit)
        self._reporter.trimmed(
            operation=operation,
            before=len(snapshot),
            after=len(trimmed),
        )
        return trimmed


class HistoryArchiver:
    """Persist history snapshots into the archive repository."""

    def __init__(
        self,
        archive: HistoryRepository,
        reporter: HistoryTelemetryReporter,
    ) -> None:
        self._archive = archive
        self._reporter = reporter

    async def save(self, history: Sequence[Entry], *, operation: str) -> None:
        """Archive ``history`` while reporting telemetry."""

        snapshot = list(history)
        await self._archive.archive(snapshot)
        self._reporter.saved(operation=operation, size=len(snapshot))


class LatestMarkerUpdater:
    """Refresh the latest message marker after persisting history."""

    def __init__(
        self,
        ledger: LatestRepository,
        reporter: HistoryTelemetryReporter,
    ) -> None:
        self._ledger = ledger
        self._reporter = reporter

    async def update(self, history: Sequence[Entry], *, operation: str) -> None:
        """Update the last message marker and emit telemetry."""

        marker = _latest_marker(history)
        if marker is None:
            return
        await self._ledger.mark(marker)
        self._reporter.marker_updated(operation=operation, message_id=marker)


class HistoryPersistencePipeline:
    """Coordinate history trimming, archiving, and marker updates."""

    def __init__(
        self,
        archive: HistoryRepository,
        ledger: LatestRepository,
        prune_history: Callable[[list[Entry], int], list[Entry]],
        limit: int,
        telemetry: Telemetry | None = None,
    ) -> None:
        reporter = HistoryTelemetryReporter(telemetry)
        self._trimmer = HistoryTrimmer(prune_history, limit, reporter)
        self._archiver = HistoryArchiver(archive, reporter)
        self._marker = LatestMarkerUpdater(ledger, reporter)

    async def persist(self, history: Sequence[Entry], *, operation: str) -> None:
        """Persist ``history`` while delegating to pipeline components."""

        trimmed = self._trimmer.apply(history, operation=operation)
        await self._archiver.save(trimmed, operation=operation)
        await self._marker.update(trimmed, operation=operation)


@dataclass(frozen=True)
class HistoryPersistencePipelineFactory:
    """Provide ready-to-use history persistence pipelines on demand."""

    archive: HistoryRepository
    ledger: LatestRepository
    prune_history: Callable[[list[Entry], int], list[Entry]]
    limit: int
    telemetry: Telemetry | None = None

    def create(self) -> HistoryPersistencePipeline:
        """Instantiate a pipeline with the configured collaborators."""

        return HistoryPersistencePipeline(
            archive=self.archive,
            ledger=self.ledger,
            prune_history=self.prune_history,
            limit=self.limit,
            telemetry=self.telemetry,
        )


async def persist(
    archive: HistoryRepository,
    ledger: LatestRepository,
    prune_history: Callable[[list[Entry], int], list[Entry]],
    limit: int,
    history: Sequence[Entry],
    *,
    operation: str,
    telemetry: Telemetry | None = None,
) -> None:
    """Persist the supplied ``history`` snapshot and update ``ledger``."""

    pipeline = HistoryPersistencePipeline(
        archive=archive,
        ledger=ledger,
        prune_history=prune_history,
        limit=limit,
        telemetry=telemetry,
    )
    await pipeline.persist(history, operation=operation)


__all__ = [
    "HistoryArchiver",
    "HistoryPersistencePipelineFactory",
    "HistoryPersistencePipeline",
    "HistoryTrimmer",
    "LatestMarkerUpdater",
    "persist",
]

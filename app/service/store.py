"""Persist conversation history with telemetry instrumentation."""

from __future__ import annotations

import logging
from collections.abc import Callable, Sequence
from dataclasses import replace

from ...core.entity.history import Entry, Message
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import Payload


def preserve(payload: Payload, entry: Message | None) -> Payload:
    """Return ``payload`` with preview and extra inherited from ``entry``."""

    if entry is None:
        return payload

    preview = _inherit(payload.preview, entry.preview)
    extra = _inherit(payload.extra, entry.extra)
    if preview is payload.preview and extra is payload.extra:
        return payload
    return replace(payload, preview=preview, extra=extra)


def _inherit(current: object | None, fallback: object | None) -> object | None:
    """Return ``current`` unless it is ``None``, falling back to ``fallback``."""

    return current if current is not None else fallback


def _channel_for(telemetry: Telemetry | None) -> TelemetryChannel | None:
    """Return a telemetry channel dedicated to storage operations."""

    return telemetry.channel(__name__) if telemetry else None


def _emit(
        channel: TelemetryChannel | None,
        level: int,
        code: LogCode,
        **payload: object,
) -> None:
    """Emit a telemetry envelope if ``channel`` is configured."""
    if channel is None:
        return
    channel.emit(level, code, **payload)


def _latest_marker(history: Sequence[Entry]) -> int | None:
    """Return the first message identifier for the most recent entry."""

    if not history:
        return None
    messages = history[-1].messages
    if not messages:
        return None
    return messages[0].id


class HistoryTrimmer:
    """Trim history snapshots according to the configured policy."""

    def __init__(
            self,
            policy: Callable[[list[Entry], int], list[Entry]],
            limit: int,
            channel: TelemetryChannel | None,
    ) -> None:
        self._policy = policy
        self._limit = limit
        self._channel = channel

    def apply(self, history: Sequence[Entry], *, operation: str) -> list[Entry]:
        """Return trimmed history while emitting telemetry when truncation occurs."""

        snapshot = list(history)
        trimmed = self._policy(snapshot, self._limit)
        if len(trimmed) != len(snapshot):
            _emit(
                self._channel,
                logging.DEBUG,
                LogCode.HISTORY_TRIM,
                op=operation,
                history={"before": len(snapshot), "after": len(trimmed)},
            )
        return trimmed


class HistoryArchiver:
    """Persist history snapshots into the archive repository."""

    def __init__(
            self,
            archive: HistoryRepository,
            channel: TelemetryChannel | None,
    ) -> None:
        self._archive = archive
        self._channel = channel

    async def save(self, history: Sequence[Entry], *, operation: str) -> None:
        """Archive ``history`` while reporting telemetry."""

        snapshot = list(history)
        await self._archive.archive(snapshot)
        _emit(
            self._channel,
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op=operation,
            history={"len": len(snapshot)},
        )


class LatestMarkerUpdater:
    """Refresh the latest message marker after persisting history."""

    def __init__(
            self,
            ledger: LatestRepository,
            channel: TelemetryChannel | None,
    ) -> None:
        self._ledger = ledger
        self._channel = channel

    async def update(self, history: Sequence[Entry], *, operation: str) -> None:
        """Update the last message marker and emit telemetry."""

        marker = _latest_marker(history)
        if marker is None:
            return
        await self._ledger.mark(marker)
        _emit(
            self._channel,
            logging.INFO,
            LogCode.LAST_SET,
            op=operation,
            message={"id": marker},
        )


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
        channel = _channel_for(telemetry)
        self._trimmer = HistoryTrimmer(prune_history, limit, channel)
        self._archiver = HistoryArchiver(archive, channel)
        self._marker = LatestMarkerUpdater(ledger, channel)

    async def persist(self, history: Sequence[Entry], *, operation: str) -> None:
        """Persist ``history`` while delegating to pipeline components."""

        trimmed = self._trimmer.apply(history, operation=operation)
        await self._archiver.save(trimmed, operation=operation)
        await self._marker.update(trimmed, operation=operation)


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

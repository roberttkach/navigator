"""Provide history operations used by the tail use-cases."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from navigator.core.entity.history import Entry
from navigator.core.port.history import HistoryRepository
from navigator.core.port.last import LatestRepository
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope


class TailHistoryScopeFormatter:
    """Convert scope objects into telemetry-friendly payloads."""

    def describe(self, scope: Scope | None) -> dict[str, object] | None:
        if scope is None:
            return None
        return {
            "chat": getattr(scope, "chat", None),
            "inline": bool(getattr(scope, "inline", None)),
            "business": bool(getattr(scope, "business", None)),
        }


class TailHistoryJournal:
    """Publish telemetry events produced by history operations."""

    def __init__(
        self,
        channel: TelemetryChannel | None,
        *,
        formatter: TailHistoryScopeFormatter | None = None,
    ) -> None:
        self._channel = channel
        self._formatter = formatter or TailHistoryScopeFormatter()

    @classmethod
    def from_telemetry(
        cls,
        telemetry: Telemetry | None,
        *,
        formatter: TailHistoryScopeFormatter | None = None,
    ) -> "TailHistoryJournal":
        channel = telemetry.channel(__name__) if telemetry else None
        return cls(channel, formatter=formatter)

    def record_marker_peek(self, marker: int | None) -> None:
        if self._channel is None:
            return
        self._channel.emit(logging.INFO, LogCode.LAST_GET, message={"id": marker})

    def record_history_load(
        self, history: Sequence[Entry], scope: Scope | None = None
    ) -> None:
        if self._channel is None:
            return
        payload: dict[str, object] = {"len": len(history)}
        described = self._formatter.describe(scope)
        kwargs: dict[str, object] = {"history": payload}
        if described is not None:
            kwargs["scope"] = described
        self._channel.emit(logging.DEBUG, LogCode.HISTORY_LOAD, **kwargs)

    def record_history_save(self, history: Sequence[Entry], *, op: str) -> None:
        if self._channel is None:
            return
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op=op,
            history={"len": len(history)},
        )

    def record_marker_mark(
        self, marker: int | None, *, op: str, scope: Scope | None = None
    ) -> None:
        if self._channel is None:
            return
        code = LogCode.LAST_SET if marker is not None else LogCode.LAST_DELETE
        payload: dict[str, object] = {"id": marker}
        described = self._formatter.describe(scope)
        if described is not None:
            payload = {"id": marker, "scope": described}
        self._channel.emit(logging.INFO, code, op=op, message=payload)


class TailHistoryStore:
    """Persist history snapshots and expose latest marker operations."""

    def __init__(self, ledger: HistoryRepository, latest: LatestRepository) -> None:
        self._ledger = ledger
        self._latest = latest

    async def peek(self) -> int | None:
        """Return the most recent marker identifier."""

        return await self._latest.peek()

    async def load(self) -> list[Entry]:
        """Load the persisted history snapshot."""

        return list(await self._ledger.recall())

    async def archive(self, history: Sequence[Entry]) -> list[Entry]:
        """Archive ``history`` and return the stored snapshot."""

        snapshot = list(history)
        await self._ledger.archive(snapshot)
        return snapshot

    async def mark(self, marker: int | None) -> None:
        """Update the latest marker with ``marker`` value."""

        await self._latest.mark(marker)


class TailHistoryAccess:
    """Encapsulate history persistence operations for tail flows."""

    def __init__(
        self,
        ledger: HistoryRepository,
        latest: LatestRepository,
        *,
        journal: TailHistoryJournal,
        store: TailHistoryStore | None = None,
    ) -> None:
        self._store = store or TailHistoryStore(ledger, latest)
        self._journal = journal

    async def peek(self) -> int | None:
        """Return the most recent marker identifier."""

        marker = await self._store.peek()
        self._journal.record_marker_peek(marker)
        return marker

    async def load(self, scope: Scope | None = None) -> list[Entry]:
        """Load the persisted history snapshot."""

        snapshot = await self._store.load()
        self._journal.record_history_load(snapshot, scope)
        return snapshot

    async def save(self, history: Sequence[Entry], *, op: str) -> None:
        """Persist ``history`` snapshot and emit telemetry."""

        snapshot = await self._store.archive(history)
        self._journal.record_history_save(snapshot, op=op)

    async def mark(
            self, marker: int | None, *, op: str, scope: Scope | None = None
    ) -> None:
        """Update the last marker and emit telemetry."""

        await self._store.mark(marker)
        self._journal.record_marker_mark(marker, op=op, scope=scope)

    async def trim_inline(
            self, history: Sequence[Entry], scope: Scope, *, op: str
    ) -> list[Entry]:
        """Trim inline history state and propagate telemetry."""

        trimmed = list(history[:-1])
        stored = await self._store.archive(trimmed)
        self._journal.record_history_save(stored, op=op)
        marker = self._latest_marker(trimmed)
        await self._store.mark(marker)
        self._journal.record_marker_mark(marker, op=op, scope=scope)
        return stored

    @staticmethod
    def _latest_marker(history: Sequence[Entry]) -> int | None:
        if not history:
            return None
        tail = history[-1]
        if not tail.messages:
            return None
        return int(tail.messages[0].id)

__all__ = [
    "TailHistoryAccess",
    "TailHistoryJournal",
    "TailHistoryScopeFormatter",
    "TailHistoryStore",
]

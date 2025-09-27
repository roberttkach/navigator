"""History reading helpers supporting rewind use case."""

from __future__ import annotations

import logging
from collections.abc import Sequence
from typing import Any

from navigator.core.entity.history import Entry
from navigator.core.error import HistoryEmpty
from navigator.core.port.history import HistoryRepository
from navigator.core.port.state import StateRepository
from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope

_MIN_HISTORY_LENGTH = 2


class RewindHistorySnapshotter:
    """Load history snapshots while reporting telemetry."""

    def __init__(self, ledger: HistoryRepository, telemetry: Telemetry) -> None:
        self._ledger = ledger
        self._channel: TelemetryChannel = telemetry.channel(
            f"{__name__}.history.snapshot"
        )

    async def load(self, scope: Scope) -> list[Entry]:
        """Return the current history snapshot."""

        history = await self._ledger.recall()
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="back",
            history={"len": len(history)},
            scope=profile(scope),
        )
        return history


class RewindHistorySelector:
    """Encapsulate selection of history entries used for rewind."""

    def select(self, history: Sequence[Entry]) -> tuple[Entry, Entry]:
        """Return the current and previous entries in ``history``."""

        if len(history) < _MIN_HISTORY_LENGTH:
            raise HistoryEmpty("Cannot go back, history is too short.")
        return history[-1], history[-2]


class RewindStateReader:
    """Expose access to persisted state payloads."""

    def __init__(self, status: StateRepository) -> None:
        self._status = status

    async def payload(self) -> dict[str, Any]:
        """Return persisted state payload used for restore operations."""

        return await self._status.payload()


__all__ = [
    "RewindHistorySnapshotter",
    "RewindHistorySelector",
    "RewindStateReader",
]

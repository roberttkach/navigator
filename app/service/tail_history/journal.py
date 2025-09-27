"""Telemetry journal for tail history operations."""
from __future__ import annotations

import logging
from collections.abc import Sequence

from navigator.core.entity.history import Entry
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope

from .formatter import TailHistoryScopeFormatter


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

    def record_history_load(self, history: Sequence[Entry], scope: Scope | None = None) -> None:
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
        self,
        marker: int | None,
        *,
        op: str,
        scope: Scope | None = None,
    ) -> None:
        if self._channel is None:
            return
        code = LogCode.LAST_SET if marker is not None else LogCode.LAST_DELETE
        payload: dict[str, object] = {"id": marker}
        described = self._formatter.describe(scope)
        if described is not None:
            payload = {"id": marker, "scope": described}
        self._channel.emit(logging.INFO, code, op=op, message=payload)


__all__ = ["TailHistoryJournal"]

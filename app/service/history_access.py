"""Provide history operations used by the tail use-cases."""

from __future__ import annotations

import logging
from collections.abc import Sequence

from navigator.core.entity.history import Entry
from navigator.core.port.history import HistoryRepository
from navigator.core.port.last import LatestRepository
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope


class TailHistoryAccess:
    """Encapsulate history persistence operations for tail flows."""

    def __init__(
            self,
            ledger: HistoryRepository,
            latest: LatestRepository,
            telemetry: Telemetry | None = None,
    ) -> None:
        self._ledger = ledger
        self._latest = latest
        self._channel: TelemetryChannel | None = (
            telemetry.channel(__name__) if telemetry else None
        )

    async def peek(self) -> int | None:
        """Return the most recent marker identifier."""

        marker = await self._latest.peek()
        self._emit(logging.INFO, LogCode.LAST_GET, message={"id": marker})
        return marker

    async def load(self, scope: Scope | None = None) -> list[Entry]:
        """Load the persisted history snapshot."""

        history = list(await self._ledger.recall())
        self._emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            scope=self._describe_scope(scope),
            history={"len": len(history)},
        )
        return history

    async def save(self, history: Sequence[Entry], *, op: str) -> None:
        """Persist ``history`` snapshot and emit telemetry."""

        snapshot = list(history)
        await self._ledger.archive(snapshot)
        self._emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op=op,
            history={"len": len(snapshot)},
        )

    async def mark(
            self, marker: int | None, *, op: str, scope: Scope | None = None
    ) -> None:
        """Update the last marker and emit telemetry."""

        await self._latest.mark(marker)
        code = LogCode.LAST_SET if marker is not None else LogCode.LAST_DELETE
        payload: dict[str, object] = {"id": marker}
        described = self._describe_scope(scope)
        if described is not None:
            payload = {"id": marker, "scope": described}
        self._emit(logging.INFO, code, op=op, message=payload)

    async def trim_inline(
            self, history: Sequence[Entry], scope: Scope, *, op: str
    ) -> list[Entry]:
        """Trim inline history state and propagate telemetry."""

        trimmed = list(history[:-1])
        await self.save(trimmed, op=op)
        marker = self._latest_marker(trimmed)
        await self.mark(marker, op=op, scope=scope)
        return trimmed

    def _emit(
            self,
            level: int,
            code: LogCode,
            /,
            **payload: object,
    ) -> None:
        if self._channel is None:
            return
        self._channel.emit(level, code, **payload)

    @staticmethod
    def _latest_marker(history: Sequence[Entry]) -> int | None:
        if not history:
            return None
        tail = history[-1]
        if not tail.messages:
            return None
        return int(tail.messages[0].id)

    @staticmethod
    def _describe_scope(scope: Scope | None) -> dict[str, object] | None:
        if scope is None:
            return None
        return {
            "chat": getattr(scope, "chat", None),
            "inline": bool(getattr(scope, "inline", None)),
            "business": bool(getattr(scope, "business", None)),
        }


__all__ = ["TailHistoryAccess"]

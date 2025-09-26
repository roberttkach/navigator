"""Telemetry helpers coordinating history pop instrumentation."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from ..log import events
from ..log.aspect import TraceAspect
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel

PerformTrim = Callable[[int], Awaitable[None]]


class PopInstrumentation:
    """Provide tracing and logging facilities for pop operations."""

    def __init__(self, telemetry: Telemetry, *, topic: str | None = None) -> None:
        channel_name = topic or "navigator.app.usecase.pop"
        self._channel: TelemetryChannel = telemetry.channel(channel_name)
        self._trace = TraceAspect(telemetry)

    async def traced(self, count: int, action: PerformTrim) -> None:
        """Execute ``action`` within the pop trace scope."""

        await self._trace.run(events.POP, action, count)

    def history_loaded(self, length: int) -> None:
        """Report history recall events."""

        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="pop",
            history={"len": length},
        )

    def history_saved(self, length: int) -> None:
        """Report history persistence events."""

        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op="pop",
            history={"len": length},
        )

    def marker_updated(self, marker: int | None) -> None:
        """Emit telemetry for latest marker updates."""

        code = LogCode.LAST_SET if marker is not None else LogCode.LAST_DELETE
        message = {"id": marker} if marker is not None else {"id": None}
        self._channel.emit(
            logging.INFO,
            code,
            op="pop",
            message=message,
        )

    def completed(self, deletions: int, remaining: int) -> None:
        """Emit telemetry for successful pop operations."""

        self._channel.emit(
            logging.INFO,
            LogCode.POP_SUCCESS,
            op="pop",
            history={"len": remaining},
            note=f"deleted:{deletions}",
        )

    def skipped(self, note: str) -> None:
        """Record pop skip decisions."""

        self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="pop", note=note)


__all__ = ["PopInstrumentation"]


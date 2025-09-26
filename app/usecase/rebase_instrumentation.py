"""Telemetry helpers dedicated to the rebase use case."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from ..log import events
from ..log.aspect import TraceAspect
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel

PerformRebase = Callable[[int], Awaitable[None]]


class RebaseInstrumentation:
    """Provide trace and logging facilities for history rebase operations."""

    def __init__(self, telemetry: Telemetry, *, topic: str | None = None) -> None:
        channel_name = topic or "navigator.app.usecase.rebase"
        self._channel: TelemetryChannel = telemetry.channel(channel_name)
        self._trace = TraceAspect(telemetry)

    async def traced(self, marker: int, action: PerformRebase) -> None:
        """Execute ``action`` within the rebase trace scope."""

        await self._trace.run(events.REBASE, action, marker)

    def history_loaded(self, length: int) -> None:
        """Report history load telemetry."""

        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="rebase",
            history={"len": length},
        )

    def history_saved(self, length: int) -> None:
        """Report history persistence telemetry."""

        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op="rebase",
            history={"len": length},
        )

    def marker_updated(self, identifier: int) -> None:
        """Emit telemetry for the updated latest marker."""

        self._channel.emit(
            logging.INFO,
            LogCode.LAST_SET,
            op="rebase",
            message={"id": identifier},
        )

    def completed(self, identifier: int, history_len: int) -> None:
        """Emit telemetry for a successful rebase operation."""

        self._channel.emit(
            logging.INFO,
            LogCode.REBASE_SUCCESS,
            op="rebase",
            message={"id": identifier},
            history={"len": history_len},
        )


__all__ = ["RebaseInstrumentation"]

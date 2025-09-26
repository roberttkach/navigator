"""Instrumentation helpers dedicated to the replace workflow."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable

from ..log import events
from ..log.aspect import TraceAspect
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import Payload
from ...core.value.message import Scope

PerformReplace = Callable[[Scope, list[Payload]], Awaitable[None]]


class ReplaceInstrumentation:
    """Coordinate tracing and telemetry for replace operations."""

    def __init__(self, telemetry: Telemetry, *, topic: str | None = None) -> None:
        channel_name = topic or "navigator.app.usecase.replace"
        self._channel: TelemetryChannel = telemetry.channel(channel_name)
        self._trace = TraceAspect(telemetry)

    async def traced(self, scope: Scope, bundle: list[Payload], action: PerformReplace) -> None:
        """Execute ``action`` within the replace trace scope."""

        await self._trace.run(events.REPLACE, action, scope, bundle)

    def render_skipped(self) -> None:
        """Emit telemetry whenever rendering is skipped."""

        self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="replace")


__all__ = ["ReplaceInstrumentation"]


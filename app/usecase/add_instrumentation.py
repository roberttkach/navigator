"""Telemetry instrumentation dedicated to append workflow."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Awaitable, Callable, List, Optional

from ..log import events
from ..log.aspect import TraceAspect
from ...core.telemetry import Telemetry, TelemetryChannel
from ...core.value.content import Payload
from ...core.value.message import Scope

AppendRunner = Callable[[Scope, List[Payload], Optional[str]], Awaitable[None]]


@dataclass(frozen=True)
class AppendInstrumentation:
    """Capture telemetry collaborators used during append orchestration."""

    channel: TelemetryChannel
    trace: TraceAspect

    @classmethod
    def from_telemetry(cls, telemetry: Telemetry) -> "AppendInstrumentation":
        return cls(channel=telemetry.channel(__name__), trace=TraceAspect(telemetry))

    async def traced(
        self,
        runner: AppendRunner,
        scope: Scope,
        bundle: List[Payload],
        view: Optional[str],
        *,
        root: bool = False,
    ) -> None:
        await self.trace.run(
            events.APPEND,
            runner,
            scope,
            bundle,
            view,
            root=root,
        )


__all__ = ["AppendInstrumentation", "AppendRunner"]

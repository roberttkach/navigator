"""Helpers assembling navigator tail services."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .contracts import TailContracts
from .tail import NavigatorTail
from .tail_components import TailGateway, TailLocker, TailTelemetry, TailViewFactory


def build_tail_service(
    contracts: TailContracts,
    *,
    guard: Guardian,
    scope: Scope,
    telemetry: Telemetry | None = None,
    tail_telemetry: TailTelemetry | None = None,
    view_factory: TailViewFactory | None = None,
) -> NavigatorTail:
    """Construct navigator tail services decoupled from other concerns."""

    gateway = TailGateway(contracts.tailer)
    locker = TailLocker(guard, scope)
    metrics = tail_telemetry
    if metrics is None:
        if telemetry is None:
            raise ValueError("telemetry or tail_telemetry must be provided")
        metrics = TailTelemetry.from_telemetry(telemetry, scope)
    factory = view_factory or TailViewFactory()
    return NavigatorTail(
        gateway=gateway,
        locker=locker,
        telemetry=metrics,
        view_factory=factory,
    )


__all__ = ["build_tail_service"]

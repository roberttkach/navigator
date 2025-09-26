"""Helpers assembling navigator tail services."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .contracts import TailContracts
from .tail import NavigatorTail
from .tail_components import TailGateway, TailLocker, TailTelemetry


def build_tail_service(
    contracts: TailContracts,
    *,
    guard: Guardian,
    scope: Scope,
    telemetry: Telemetry,
) -> NavigatorTail:
    """Construct navigator tail services decoupled from other concerns."""

    gateway = TailGateway(contracts.tailer)
    locker = TailLocker(guard, scope)
    tail_telemetry = TailTelemetry.from_telemetry(telemetry, scope)
    return NavigatorTail(gateway=gateway, locker=locker, telemetry=tail_telemetry)


__all__ = ["build_tail_service"]

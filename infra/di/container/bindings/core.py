"""Core binding container aggregating foundational dependencies."""

from __future__ import annotations

from dependency_injector import containers, providers

from navigator.adapters.storage.fsm.context import StateContext
from navigator.core.port.factory import ViewLedger
from navigator.core.telemetry import Telemetry

from ..core import CoreContainer


class CoreBindings(containers.DeclarativeContainer):
    """Expose base dependencies shared across modules."""

    event = providers.Dependency()
    state = providers.Dependency(instance_of=StateContext)
    ledger = providers.Dependency(instance_of=ViewLedger)
    alert = providers.Dependency()
    telemetry = providers.Dependency(instance_of=Telemetry)

    core = providers.Container(
        CoreContainer,
        event=event,
        state=state,
        ledger=ledger,
        alert=alert,
        telemetry=telemetry,
    )


__all__ = ["CoreBindings"]

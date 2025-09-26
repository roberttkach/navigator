"""Application dependency injection container."""
from __future__ import annotations

from aiogram.fsm.context import FSMContext
from dependency_injector import containers, providers
from navigator.core.port.factory import ViewLedger
from navigator.core.telemetry import Telemetry

from .core import CoreContainer
from .storage import StorageContainer
from .telegram import TelegramContainer
from .runtime import NavigatorRuntimeContainer
from .usecases import UseCaseContainer


class AppContainer(containers.DeclarativeContainer):
    event = providers.Dependency()
    state = providers.Dependency(instance_of=FSMContext)
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
    storage = providers.Container(StorageContainer, core=core, telemetry=telemetry)
    view = providers.Container(TelegramContainer, core=core, telemetry=telemetry)
    usecases = providers.Container(
        UseCaseContainer,
        core=core,
        storage=storage,
        view=view,
        telemetry=telemetry,
    )
    runtime = providers.Container(
        NavigatorRuntimeContainer,
        core=core,
        usecases=usecases,
        telemetry=telemetry,
    )


__all__ = ["AppContainer"]

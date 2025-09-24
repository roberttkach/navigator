"""Application dependency injection container."""
from __future__ import annotations

from aiogram.fsm.context import FSMContext
from dependency_injector import containers, providers

from navigator.core.port.factory import ViewLedger
from .core import CoreContainer
from .storage import StorageContainer
from .telegram import TelegramContainer
from .usecases import UseCaseContainer


class AppContainer(containers.DeclarativeContainer):
    event = providers.Dependency()
    state = providers.Dependency(instance_of=FSMContext)
    ledger = providers.Dependency(instance_of=ViewLedger)
    alert = providers.Dependency()

    core = providers.Container(
        CoreContainer,
        event=event,
        state=state,
        ledger=ledger,
        alert=alert,
    )
    storage = providers.Container(StorageContainer, core=core)
    telegram = providers.Container(TelegramContainer, core=core)
    usecases = providers.Container(UseCaseContainer, core=core, storage=storage, telegram=telegram)


__all__ = ["AppContainer"]

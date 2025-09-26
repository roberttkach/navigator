"""Navigator use case container wiring composed from domain modules."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.usecase.alarm import Alarm
from navigator.app.service.navigator_runtime import NavigatorUseCases
from navigator.core.telemetry import Telemetry

from .history import HistoryUseCaseContainer
from .tail import TailUseCaseContainer


class UseCaseContainer(containers.DeclarativeContainer):
    """Assemble navigator-specific use cases from modular containers."""

    core = providers.DependenciesContainer()
    storage = providers.DependenciesContainer()
    view_support = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    history = providers.Container(
        HistoryUseCaseContainer,
        core=core,
        storage=storage,
        telemetry=telemetry,
        view_support=view_support,
    )
    tail = providers.Container(
        TailUseCaseContainer,
        core=core,
        storage=storage,
        view_support=view_support,
        telemetry=telemetry,
    )
    alarm = providers.Factory(
        Alarm,
        gateway=view_support.gateway,
        alert=core.alert,
        telemetry=telemetry,
    )
    navigator = providers.Factory(
        NavigatorUseCases,
        appender=history.provided.appender,
        swapper=history.provided.swapper,
        rewinder=history.provided.rewinder,
        setter=history.provided.setter,
        trimmer=history.provided.trimmer,
        shifter=history.provided.shifter,
        tailer=tail.provided.tailer,
        alarm=alarm,
    )


__all__ = ["UseCaseContainer"]

"""History-related use case containers composed for navigator runtime."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.core.telemetry import Telemetry

from .append import AppendUseCaseContainer
from .maintenance import MaintenanceUseCaseContainer
from .replace import ReplaceUseCaseContainer
from .rewind import RewindUseCaseContainer
from .state import StateUseCaseContainer


class HistoryUseCaseContainer(containers.DeclarativeContainer):
    """Compose history-oriented use cases from storage and view helpers."""

    core = providers.DependenciesContainer()
    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)
    view_support = providers.DependenciesContainer()

    append = providers.Container(
        AppendUseCaseContainer,
        storage=storage,
        telemetry=telemetry,
        view_support=view_support,
        history_limit=core.settings.provided.historylimit,
    )
    replace = providers.Container(
        ReplaceUseCaseContainer,
        storage=storage,
        telemetry=telemetry,
        view_support=view_support,
        history_limit=core.settings.provided.historylimit,
    )
    rewind = providers.Container(
        RewindUseCaseContainer,
        storage=storage,
        telemetry=telemetry,
        view_support=view_support,
    )
    state_ops = providers.Container(
        StateUseCaseContainer,
        storage=storage,
        telemetry=telemetry,
        view_support=view_support,
    )
    maintenance = providers.Container(
        MaintenanceUseCaseContainer,
        storage=storage,
        telemetry=telemetry,
    )

    appender = append.provided.usecase
    swapper = replace.provided.usecase
    rewinder = rewind.provided.usecase
    setter = state_ops.provided.setter
    trimmer = maintenance.provided.trimmer
    shifter = maintenance.provided.shifter


__all__ = ["HistoryUseCaseContainer"]

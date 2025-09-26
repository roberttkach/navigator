"""Container providing append-oriented history use case wiring."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.usecase.add import AppendDependencies, Appender
from navigator.app.usecase.add_components import (
    AppendHistoryAccess,
    AppendHistoryJournal,
    AppendHistoryWriter,
    AppendPreparation,
)
from navigator.core.telemetry import Telemetry


class AppendUseCaseContainer(containers.DeclarativeContainer):
    """Bundle append collaborators to keep the history container lean."""

    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)
    view_support = providers.DependenciesContainer()
    history_limit = providers.Dependency()

    journal = providers.Factory(AppendHistoryJournal, telemetry=telemetry)
    history = providers.Factory(
        AppendHistoryAccess,
        archive=storage.chronicle,
        state=storage.status,
        observer=journal,
    )
    preparation = providers.Factory(
        AppendPreparation,
        planner=view_support.planner,
        mapper=storage.mapper,
    )
    writer = providers.Factory(
        AppendHistoryWriter,
        archive=storage.chronicle,
        tail=storage.latest,
        limit=history_limit,
        telemetry=telemetry,
    )
    bundle = providers.Factory(
        AppendDependencies,
        history=history,
        preparation=preparation,
        writer=writer,
    )
    usecase = providers.Factory(
        Appender,
        telemetry=telemetry,
        dependencies=bundle,
    )


__all__ = ["AppendUseCaseContainer"]

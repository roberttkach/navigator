"""Container wiring history replace use case collaborators."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.usecase.replace import Swapper
from navigator.app.usecase.replace_components import (
    ReplaceHistoryAccess,
    ReplaceHistoryWriter,
    ReplacePreparation,
    ReplaceHistoryJournal,
)
from navigator.app.usecase.replace_instrumentation import ReplaceInstrumentation
from navigator.core.telemetry import Telemetry


class ReplaceUseCaseContainer(containers.DeclarativeContainer):
    """Construct replace-related collaborators in isolation."""

    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)
    view_support = providers.DependenciesContainer()
    history_limit = providers.Dependency()

    history_observer = providers.Factory(
        ReplaceHistoryJournal,
        telemetry=telemetry,
    )
    history = providers.Factory(
        ReplaceHistoryAccess,
        archive=storage.chronicle,
        state=storage.status,
        observer=history_observer,
    )
    preparation = providers.Factory(
        ReplacePreparation,
        planner=view_support.planner,
        mapper=storage.mapper,
    )
    writer = providers.Factory(
        ReplaceHistoryWriter,
        archive=storage.chronicle,
        tail=storage.latest,
        limit=history_limit,
        telemetry=telemetry,
    )
    instrumentation = providers.Factory(
        ReplaceInstrumentation,
        telemetry=telemetry,
    )
    usecase = providers.Factory(
        Swapper,
        history=history,
        preparation=preparation,
        writer=writer,
        instrumentation=instrumentation,
    )


__all__ = ["ReplaceUseCaseContainer"]

"""Container building history-related navigator use cases."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.usecase.add import AppendDependencies, Appender
from navigator.app.usecase.add_components import (
    AppendHistoryAccess,
    AppendHistoryWriter,
    AppendPreparation,
)
from navigator.app.usecase.back import Rewinder
from navigator.app.usecase.back_access import (
    RewindFinalizer,
    RewindHistoryReader,
    RewindHistoryWriter,
    RewindMutator,
    RewindRenderer,
)
from navigator.app.usecase.pop import Trimmer
from navigator.app.usecase.rebase import Shifter
from navigator.app.usecase.replace import Swapper
from navigator.app.usecase.replace_components import (
    ReplaceHistoryAccess,
    ReplaceHistoryWriter,
    ReplacePreparation,
)
from navigator.app.usecase.set import Setter
from navigator.app.usecase.set_components import (
    HistoryReconciler,
    HistoryRestorationPlanner,
    PayloadReviver,
    StateSynchronizer,
)
from navigator.core.telemetry import Telemetry


class HistoryUseCaseContainer(containers.DeclarativeContainer):
    """Compose history-oriented use cases from storage and view helpers."""

    core = providers.DependenciesContainer()
    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)
    view_support = providers.DependenciesContainer()

    append_history = providers.Factory(
        AppendHistoryAccess,
        archive=storage.chronicle,
        state=storage.status,
        telemetry=telemetry,
    )
    append_preparation = providers.Factory(
        AppendPreparation,
        planner=view_support.planner,
        mapper=storage.mapper,
    )
    append_writer = providers.Factory(
        AppendHistoryWriter,
        archive=storage.chronicle,
        tail=storage.latest,
        limit=core.settings.provided.historylimit,
        telemetry=telemetry,
    )
    append_dependencies = providers.Factory(
        AppendDependencies,
        history=append_history,
        preparation=append_preparation,
        writer=append_writer,
    )
    appender = providers.Factory(
        Appender,
        telemetry=telemetry,
        dependencies=append_dependencies,
    )
    replace_history = providers.Factory(
        ReplaceHistoryAccess,
        archive=storage.chronicle,
        state=storage.status,
        telemetry=telemetry,
    )
    replace_preparation = providers.Factory(
        ReplacePreparation,
        planner=view_support.planner,
        mapper=storage.mapper,
    )
    replace_writer = providers.Factory(
        ReplaceHistoryWriter,
        archive=storage.chronicle,
        tail=storage.latest,
        limit=core.settings.provided.historylimit,
        telemetry=telemetry,
    )
    swapper = providers.Factory(
        Swapper,
        history=replace_history,
        preparation=replace_preparation,
        writer=replace_writer,
        telemetry=telemetry,
    )
    rewind_reader = providers.Factory(
        RewindHistoryReader,
        ledger=storage.chronicle,
        status=storage.status,
        telemetry=telemetry,
    )
    rewind_writer = providers.Factory(
        RewindHistoryWriter,
        ledger=storage.chronicle,
        status=storage.status,
        latest=storage.latest,
        telemetry=telemetry,
    )
    rewind_renderer = providers.Factory(
        RewindRenderer,
        restorer=view_support.restorer,
        planner=view_support.planner,
    )
    rewind_mutator = providers.Factory(RewindMutator)
    rewind_finalizer = providers.Factory(
        RewindFinalizer,
        writer=rewind_writer,
        mutator=rewind_mutator,
        telemetry=telemetry,
    )
    rewinder = providers.Factory(
        Rewinder,
        history=rewind_reader,
        writer=rewind_writer,
        renderer=rewind_renderer,
        mutator=rewind_mutator,
        finalizer=rewind_finalizer,
        telemetry=telemetry,
    )
    state_sync = providers.Factory(StateSynchronizer, state=storage.status, telemetry=telemetry)
    restoration_planner = providers.Factory(
        HistoryRestorationPlanner,
        ledger=storage.chronicle,
        telemetry=telemetry,
    )
    payload_reviver = providers.Factory(
        PayloadReviver,
        synchronizer=state_sync,
        restorer=view_support.restorer,
    )
    history_reconciler = providers.Factory(
        HistoryReconciler,
        ledger=storage.chronicle,
        latest=storage.latest,
        telemetry=telemetry,
    )
    setter = providers.Factory(
        Setter,
        planner=restoration_planner,
        state=state_sync,
        reviver=payload_reviver,
        renderer=view_support.planner,
        reconciler=history_reconciler,
        telemetry=telemetry,
    )
    trimmer = providers.Factory(
        Trimmer,
        ledger=storage.chronicle,
        latest=storage.latest,
        telemetry=telemetry,
    )
    shifter = providers.Factory(
        Shifter,
        ledger=storage.chronicle,
        latest=storage.latest,
        telemetry=telemetry,
    )

__all__ = ["HistoryUseCaseContainer"]

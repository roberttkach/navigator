"""Container building history-related navigator use cases."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.usecase.add import AppendDependencies, Appender
from navigator.app.usecase.add_components import (
    AppendHistoryAccess,
    AppendHistoryJournal,
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


class ReplaceUseCaseContainer(containers.DeclarativeContainer):
    """Construct replace-related collaborators in isolation."""

    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)
    view_support = providers.DependenciesContainer()
    history_limit = providers.Dependency()

    history = providers.Factory(
        ReplaceHistoryAccess,
        archive=storage.chronicle,
        state=storage.status,
        telemetry=telemetry,
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
    usecase = providers.Factory(
        Swapper,
        history=history,
        preparation=preparation,
        writer=writer,
        telemetry=telemetry,
    )


class RewindUseCaseContainer(containers.DeclarativeContainer):
    """Group rewinder dependencies to avoid sprawling provider lists."""

    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)
    view_support = providers.DependenciesContainer()

    reader = providers.Factory(
        RewindHistoryReader,
        ledger=storage.chronicle,
        status=storage.status,
        telemetry=telemetry,
    )
    writer = providers.Factory(
        RewindHistoryWriter,
        ledger=storage.chronicle,
        status=storage.status,
        latest=storage.latest,
        telemetry=telemetry,
    )
    renderer = providers.Factory(
        RewindRenderer,
        restorer=view_support.restorer,
        planner=view_support.planner,
    )
    mutator = providers.Factory(RewindMutator)
    finalizer = providers.Factory(
        RewindFinalizer,
        writer=writer,
        mutator=mutator,
        telemetry=telemetry,
    )
    usecase = providers.Factory(
        Rewinder,
        history=reader,
        writer=writer,
        renderer=renderer,
        mutator=mutator,
        finalizer=finalizer,
        telemetry=telemetry,
    )


class StateUseCaseContainer(containers.DeclarativeContainer):
    """Compose setter-related collaborators behind a focused container."""

    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)
    view_support = providers.DependenciesContainer()

    synchronizer = providers.Factory(StateSynchronizer, state=storage.status, telemetry=telemetry)
    planner = providers.Factory(
        HistoryRestorationPlanner,
        ledger=storage.chronicle,
        telemetry=telemetry,
    )
    reviver = providers.Factory(
        PayloadReviver,
        synchronizer=synchronizer,
        restorer=view_support.restorer,
    )
    reconciler = providers.Factory(
        HistoryReconciler,
        ledger=storage.chronicle,
        latest=storage.latest,
        telemetry=telemetry,
    )
    setter = providers.Factory(
        Setter,
        planner=planner,
        state=synchronizer,
        reviver=reviver,
        renderer=view_support.planner,
        reconciler=reconciler,
        telemetry=telemetry,
    )


class MaintenanceUseCaseContainer(containers.DeclarativeContainer):
    """Provide history maintenance helpers (trim and shift)."""

    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

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

    append_history = append.provided.history
    append_preparation = append.provided.preparation
    append_writer = append.provided.writer
    append_dependencies = append.provided.bundle
    appender = append.provided.usecase

    replace_history = replace.provided.history
    replace_preparation = replace.provided.preparation
    replace_writer = replace.provided.writer
    swapper = replace.provided.usecase

    rewind_reader = rewind.provided.reader
    rewind_writer = rewind.provided.writer
    rewind_renderer = rewind.provided.renderer
    rewind_mutator = rewind.provided.mutator
    rewind_finalizer = rewind.provided.finalizer
    rewinder = rewind.provided.usecase

    state_sync = state_ops.provided.synchronizer
    restoration_planner = state_ops.provided.planner
    payload_reviver = state_ops.provided.reviver
    history_reconciler = state_ops.provided.reconciler
    setter = state_ops.provided.setter

    trimmer = maintenance.provided.trimmer
    shifter = maintenance.provided.shifter

__all__ = ["HistoryUseCaseContainer"]

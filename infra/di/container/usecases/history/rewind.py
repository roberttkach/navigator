"""Container configuring rewind (back) history use cases."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.usecase.back import RewindInstrumentation, RewindPerformer, Rewinder
from navigator.app.usecase.back_access import (
    RewindFinalizer,
    RewindHistoryArchiver,
    RewindHistorySelector,
    RewindHistorySnapshotter,
    RewindLatestMarker,
    RewindMutator,
    RewindRenderer,
    RewindStateReader,
    RewindStateWriter,
    RewindWriteTelemetry,
)
from navigator.core.telemetry import Telemetry


class RewindUseCaseContainer(containers.DeclarativeContainer):
    """Group rewinder dependencies to avoid sprawling provider lists."""

    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)
    view_support = providers.DependenciesContainer()

    history_snapshotter = providers.Factory(
        RewindHistorySnapshotter,
        ledger=storage.chronicle,
        telemetry=telemetry,
    )
    history_selector = providers.Factory(RewindHistorySelector)
    state_reader = providers.Factory(
        RewindStateReader,
        status=storage.status,
    )
    writer_instrumentation = providers.Factory(
        RewindWriteTelemetry,
        telemetry=telemetry,
    )
    history_archiver = providers.Factory(
        RewindHistoryArchiver,
        ledger=storage.chronicle,
        instrumentation=writer_instrumentation,
    )
    state_writer = providers.Factory(
        RewindStateWriter,
        status=storage.status,
        instrumentation=writer_instrumentation,
    )
    latest_marker = providers.Factory(
        RewindLatestMarker,
        latest=storage.latest,
        instrumentation=writer_instrumentation,
    )
    renderer = providers.Factory(
        RewindRenderer,
        restorer=view_support.restorer,
        planner=view_support.planner,
    )
    mutator = providers.Factory(RewindMutator)
    finalizer = providers.Factory(
        RewindFinalizer,
        archiver=history_archiver,
        state=state_writer,
        latest=latest_marker,
        mutator=mutator,
        telemetry=telemetry,
    )
    instrumentation = providers.Factory(
        RewindInstrumentation,
        telemetry=telemetry,
    )
    performer = providers.Factory(
        RewindPerformer,
        snapshotter=history_snapshotter,
        selector=history_selector,
        state=state_reader,
        renderer=renderer,
        finalizer=finalizer,
    )
    usecase = providers.Factory(
        Rewinder,
        performer=performer,
        instrumentation=instrumentation,
    )


__all__ = ["RewindUseCaseContainer"]

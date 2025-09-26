"""Container configuring rewind (back) history use cases."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.usecase.back import Rewinder
from navigator.app.usecase.back_access import (
    RewindFinalizer,
    RewindHistoryReader,
    RewindHistoryWriter,
    RewindMutator,
    RewindRenderer,
    RewindWriteTelemetry,
)
from navigator.core.telemetry import Telemetry


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
    writer_instrumentation = providers.Factory(
        RewindWriteTelemetry,
        telemetry=telemetry,
    )
    writer = providers.Factory(
        RewindHistoryWriter,
        ledger=storage.chronicle,
        status=storage.status,
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


__all__ = ["RewindUseCaseContainer"]

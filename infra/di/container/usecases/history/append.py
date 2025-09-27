"""Container providing append-oriented history use case wiring."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.usecase.add import (
    AppendDependencies,
    AppendInstrumentation,
    AppendPipelineFactory,
    AppendWorkflow,
    Appender,
)
from navigator.app.usecase.add_components import (
    AppendEntryAssembler,
    AppendHistoryJournal,
    AppendHistoryWriter,
    AppendPayloadAdapter,
    AppendRenderPlanner,
    HistorySnapshotAccess,
    StateStatusAccess,
)
from navigator.core.telemetry import Telemetry


class AppendUseCaseContainer(containers.DeclarativeContainer):
    """Bundle append collaborators to keep the history container lean."""

    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)
    view_support = providers.DependenciesContainer()
    history_limit = providers.Dependency()

    journal = providers.Factory(AppendHistoryJournal, telemetry=telemetry)
    history_snapshot = providers.Factory(
        HistorySnapshotAccess,
        archive=storage.chronicle,
        observer=journal,
    )
    state_status = providers.Factory(
        StateStatusAccess,
        state=storage.status,
        observer=journal,
    )
    payloads = providers.Factory(AppendPayloadAdapter)
    planner = providers.Factory(AppendRenderPlanner, planner=view_support.planner)
    assembler = providers.Factory(AppendEntryAssembler, mapper=storage.mapper)
    writer = providers.Factory(
        AppendHistoryWriter,
        archive=storage.chronicle,
        tail=storage.latest,
        limit=history_limit,
        telemetry=telemetry,
    )
    bundle = providers.Factory(
        AppendDependencies,
        history=history_snapshot,
        state=state_status,
        payloads=payloads,
        planner=planner,
        assembler=assembler,
        writer=writer,
    )
    pipeline_factory = providers.Factory(
        AppendPipelineFactory,
        dependencies=bundle,
    )
    instrumentation = providers.Factory(
        AppendInstrumentation.from_telemetry,
        telemetry=telemetry,
    )
    workflow = providers.Factory(
        AppendWorkflow.from_factory,
        factory=pipeline_factory,
        channel=instrumentation.provided.channel,
    )
    usecase = providers.Factory(
        Appender,
        instrumentation=instrumentation,
        workflow=workflow,
    )


__all__ = ["AppendUseCaseContainer"]

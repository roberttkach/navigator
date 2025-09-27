"""Container providing append-oriented history use case wiring."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.usecase.add import (
    AppendInstrumentation,
    AppendPipelineFactory,
    AppendPreparationFactory,
    AppendPersistenceFactory,
    AppendRenderingFactory,
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
from navigator.app.service.store import HistoryPersistencePipelineFactory
from navigator.core.telemetry import Telemetry
from navigator.core.service.history.policy import prune as prune_history


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
    history_pipeline_factory = providers.Factory(
        HistoryPersistencePipelineFactory,
        archive=storage.chronicle,
        ledger=storage.latest,
        prune_history=prune_history,
        limit=history_limit,
        telemetry=telemetry,
    )
    writer = providers.Factory(
        AppendHistoryWriter,
        pipeline_factory=history_pipeline_factory,
    )
    preparation_factory = providers.Factory(
        AppendPreparationFactory,
        history=history_snapshot,
        payloads=payloads,
    )
    rendering_factory = providers.Factory(
        AppendRenderingFactory,
        planner=planner,
    )
    persistence_factory = providers.Factory(
        AppendPersistenceFactory,
        state=state_status,
        assembler=assembler,
        writer=writer,
    )
    append_pipeline_factory = providers.Factory(
        AppendPipelineFactory,
        preparation=preparation_factory,
        rendering=rendering_factory,
        persistence=persistence_factory,
    )
    instrumentation = providers.Factory(
        AppendInstrumentation.from_telemetry,
        telemetry=telemetry,
    )
    workflow = providers.Factory(
        AppendWorkflow.from_factory,
        factory=append_pipeline_factory,
        channel=instrumentation.provided.channel,
    )
    usecase = providers.Factory(
        Appender,
        instrumentation=instrumentation,
        workflow=workflow,
    )


__all__ = ["AppendUseCaseContainer"]

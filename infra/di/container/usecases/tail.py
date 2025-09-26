"""Container building tail-oriented navigator use cases."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.service import (
    TailHistoryAccess,
    TailHistoryJournal,
    TailHistoryMutator,
    TailHistoryTracker,
)
from navigator.app.usecase.last import Tailer
from navigator.app.usecase.last.context import TailDecisionService, TailTelemetry
from navigator.app.internal.policy import PrimeEntryFactory
from navigator.app.usecase.last.delete import TailDeleteWorkflow
from navigator.app.usecase.last.edit import TailEditWorkflow
from navigator.app.usecase.last.inline import InlineEditCoordinator
from navigator.app.usecase.last.mutation import MessageEditCoordinator
from navigator.core.telemetry import Telemetry


class TailUseCaseContainer(containers.DeclarativeContainer):
    """Compose tail-related services for the navigator runtime."""

    core = providers.DependenciesContainer()
    storage = providers.DependenciesContainer()
    view = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    tail_history_journal = providers.Factory(
        TailHistoryJournal.from_telemetry,
        telemetry=telemetry,
    )
    tail_history_access = providers.Factory(
        TailHistoryAccess,
        ledger=storage.chronicle,
        latest=storage.latest,
    )
    tail_history = providers.Factory(
        TailHistoryTracker,
        access=tail_history_access,
        journal=tail_history_journal,
    )
    tail_mutator = providers.Factory(TailHistoryMutator)
    tail_prime = providers.Factory(PrimeEntryFactory, clock=core.clock)
    tail_decision = providers.Factory(
        TailDecisionService,
        rendering=core.rendering,
        prime=tail_prime,
    )
    tail_inline = providers.Factory(
        InlineEditCoordinator,
        handler=view.inline,
        executor=view.executor,
        rendering=core.rendering,
    )
    tail_mutation = providers.Factory(
        MessageEditCoordinator,
        executor=view.executor,
        history=tail_history,
        mutator=tail_mutator,
    )
    tail_telemetry = providers.Factory(TailTelemetry, telemetry=telemetry)
    tail_delete = providers.Factory(
        TailDeleteWorkflow,
        history=tail_history,
        mutation=tail_mutation,
        telemetry=tail_telemetry,
    )
    tail_edit = providers.Factory(
        TailEditWorkflow,
        history=tail_history,
        decision=tail_decision,
        inline=tail_inline,
        mutation=tail_mutation,
        telemetry=tail_telemetry,
    )
    tailer = providers.Factory(
        Tailer,
        history=tail_history,
        delete=tail_delete,
        edit=tail_edit,
    )


__all__ = ["TailUseCaseContainer"]

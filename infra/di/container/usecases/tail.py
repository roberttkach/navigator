"""Container building tail-oriented navigator use cases."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.service import TailHistoryMutator
from navigator.app.service.tail_history import (
    TailHistoryAccess,
    TailHistoryJournal,
    TailHistoryReader,
    TailHistoryWriter,
    TailInlineHistory,
    TailInlineTrimmer,
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
    view_support = providers.DependenciesContainer()
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
    tail_history_reader = providers.Factory(
        TailHistoryReader,
        access=tail_history_access,
        journal=tail_history_journal,
    )
    tail_history_writer = providers.Factory(
        TailHistoryWriter,
        access=tail_history_access,
        journal=tail_history_journal,
    )
    tail_inline_trimmer = providers.Factory(
        TailInlineTrimmer,
        store=tail_history_access.provided.store,
    )
    tail_inline_history = providers.Factory(
        TailInlineHistory,
        trimmer=tail_inline_trimmer,
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
        handler=view_support.inline,
        executor=view_support.executor,
        rendering=core.rendering,
    )
    tail_mutation = providers.Factory(
        MessageEditCoordinator,
        executor=view_support.executor,
        history=tail_history_writer,
        mutator=tail_mutator,
    )
    tail_telemetry = providers.Factory(TailTelemetry, telemetry=telemetry)
    tail_delete = providers.Factory(
        TailDeleteWorkflow,
        reader=tail_history_reader,
        inline_history=tail_inline_history,
        mutation=tail_mutation,
        telemetry=tail_telemetry,
    )
    tail_edit = providers.Factory(
        TailEditWorkflow,
        reader=tail_history_reader,
        decision=tail_decision,
        inline=tail_inline,
        mutation=tail_mutation,
        telemetry=tail_telemetry,
    )
    tailer = providers.Factory(
        Tailer,
        history=tail_history_reader,
        delete=tail_delete,
        edit=tail_edit,
    )


__all__ = ["TailUseCaseContainer"]

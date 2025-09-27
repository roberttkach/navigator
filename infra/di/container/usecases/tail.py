"""Container building tail-oriented navigator use cases."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.internal.policy import PrimeEntryFactory
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
from navigator.app.usecase.last.delete import TailDeleteWorkflow
from navigator.app.usecase.last.edit import TailEditWorkflow
from navigator.app.usecase.last.inline import InlineEditCoordinator
from navigator.app.usecase.last.mutation import MessageEditCoordinator
from navigator.core.telemetry import Telemetry


class TailHistoryContainer(containers.DeclarativeContainer):
    """Provide access and journaling helpers for tail history operations."""

    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    journal = providers.Factory(
        TailHistoryJournal.from_telemetry,
        telemetry=telemetry,
    )
    access = providers.Factory(
        TailHistoryAccess,
        ledger=storage.chronicle,
        latest=storage.latest,
    )
    reader = providers.Factory(
        TailHistoryReader,
        access=access,
        journal=journal,
    )
    writer = providers.Factory(
        TailHistoryWriter,
        access=access,
        journal=journal,
    )
    inline_trimmer = providers.Factory(
        TailInlineTrimmer,
        store=access.provided.store,
    )
    inline_history = providers.Factory(
        TailInlineHistory,
        trimmer=inline_trimmer,
        journal=journal,
    )


class TailDecisionContainer(containers.DeclarativeContainer):
    """Compose helpers that make tail decisions based on current context."""

    core = providers.DependenciesContainer()
    storage = providers.DependenciesContainer()

    prime = providers.Factory(
        PrimeEntryFactory,
        clock=core.clock,
        entities=storage.entities,
    )
    decision = providers.Factory(
        TailDecisionService,
        rendering=core.rendering,
        prime=prime,
    )


class TailInlineContainer(containers.DeclarativeContainer):
    """Manage inline edit orchestration and mutations for the tail."""

    core = providers.DependenciesContainer()
    view_support = providers.DependenciesContainer()
    history = providers.DependenciesContainer()

    mutator = providers.Factory(TailHistoryMutator)
    inline = providers.Factory(
        InlineEditCoordinator,
        handler=view_support.inline,
        executor=view_support.executor,
        rendering=core.rendering,
    )
    mutation = providers.Factory(
        MessageEditCoordinator,
        executor=view_support.executor,
        history=history.writer,
        mutator=mutator,
    )


class TailWorkflowContainer(containers.DeclarativeContainer):
    """Bundle tail workflows and expose high level executors."""

    history = providers.DependenciesContainer()
    inline = providers.DependenciesContainer()
    decision = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    tail_telemetry = providers.Factory(TailTelemetry, telemetry=telemetry)
    delete = providers.Factory(
        TailDeleteWorkflow,
        reader=history.reader,
        inline_history=history.inline_history,
        mutation=inline.mutation,
        telemetry=tail_telemetry,
    )
    edit = providers.Factory(
        TailEditWorkflow,
        reader=history.reader,
        decision=decision.decision,
        inline=inline.inline,
        mutation=inline.mutation,
        telemetry=tail_telemetry,
    )
    tailer = providers.Factory(
        Tailer,
        history=history.reader,
        delete=delete,
        edit=edit,
    )


class TailUseCaseContainer(containers.DeclarativeContainer):
    """Compose tail-related services for the navigator runtime."""

    core = providers.DependenciesContainer()
    storage = providers.DependenciesContainer()
    view_support = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    history = providers.Container(
        TailHistoryContainer,
        storage=storage,
        telemetry=telemetry,
    )
    decisions = providers.Container(
        TailDecisionContainer,
        core=core,
        storage=storage,
    )
    inline = providers.Container(
        TailInlineContainer,
        core=core,
        view_support=view_support,
        history=history,
    )
    workflows = providers.Container(
        TailWorkflowContainer,
        history=history,
        inline=inline,
        decision=decisions,
        telemetry=telemetry,
    )

    tail_history_journal = history.provided.journal
    tail_history_access = history.provided.access
    tail_history_reader = history.provided.reader
    tail_history_writer = history.provided.writer
    tail_inline_trimmer = history.provided.inline_trimmer
    tail_inline_history = history.provided.inline_history
    tail_prime = decisions.provided.prime
    tail_decision = decisions.provided.decision
    tail_inline = inline.provided.inline
    tail_mutation = inline.provided.mutation
    tail_delete = workflows.provided.delete
    tail_edit = workflows.provided.edit
    tailer = workflows.provided.tailer


__all__ = ["TailUseCaseContainer"]

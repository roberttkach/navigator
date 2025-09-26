"""Container building tail-oriented navigator use cases."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.service import TailHistoryAccess, TailHistoryMutator
from navigator.app.usecase.last import Tailer
from navigator.app.usecase.last.context import TailDecisionService, TailTelemetry
from navigator.app.usecase.last.inline import InlineEditCoordinator
from navigator.app.usecase.last.mutation import MessageEditCoordinator
from navigator.core.telemetry import Telemetry


class TailUseCaseContainer(containers.DeclarativeContainer):
    """Compose tail-related services for the navigator runtime."""

    core = providers.DependenciesContainer()
    storage = providers.DependenciesContainer()
    view = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    tail_history = providers.Factory(
        TailHistoryAccess,
        ledger=storage.chronicle,
        latest=storage.latest,
        telemetry=telemetry,
    )
    tail_mutator = providers.Factory(TailHistoryMutator)
    tail_decision = providers.Factory(TailDecisionService, rendering=core.rendering)
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
    tailer = providers.Factory(
        Tailer,
        history=tail_history,
        decision=tail_decision,
        inline=tail_inline,
        mutation=tail_mutation,
        telemetry=tail_telemetry,
    )


__all__ = ["TailUseCaseContainer"]

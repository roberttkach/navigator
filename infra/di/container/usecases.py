from __future__ import annotations

from dependency_injector import containers, providers
from navigator.app.service import TailHistoryAccess, TailHistoryMutator
from navigator.app.service.view.planner import (
    InlineRenderPlanner,
    RegularRenderPlanner,
    RenderSynchronizer,
    TailOperations,
    ViewPlanner,
)
from navigator.app.service.view.restorer import ViewRestorer
from navigator.app.usecase.add import Appender
from navigator.app.usecase.alarm import Alarm
from navigator.app.usecase.back import Rewinder
from navigator.app.usecase.last import Tailer
from navigator.app.usecase.last.context import TailDecisionService, TailTelemetry
from navigator.app.usecase.last.inline import InlineEditCoordinator
from navigator.app.usecase.last.mutation import MessageEditCoordinator
from navigator.app.usecase.pop import Trimmer
from navigator.app.usecase.rebase import Shifter
from navigator.app.usecase.replace import Swapper
from navigator.app.usecase.set import Setter
from navigator.core.telemetry import Telemetry


class UseCaseContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()
    storage = providers.DependenciesContainer()
    view = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    render_synchronizer = providers.Factory(
        RenderSynchronizer,
        executor=view.executor,
        inline=view.inline,
        rendering=core.rendering,
    )
    tail_operations = providers.Factory(TailOperations, executor=view.executor, rendering=core.rendering)
    inline_planner = providers.Factory(InlineRenderPlanner, synchronizer=render_synchronizer)
    regular_planner = providers.Factory(
        RegularRenderPlanner,
        album=view.album,
        synchronizer=render_synchronizer,
        tails=tail_operations,
        telemetry=telemetry,
    )
    planner = providers.Factory(
        ViewPlanner,
        inline=inline_planner,
        regular=regular_planner,
    )
    restorer = providers.Factory(ViewRestorer, ledger=core.ledger, telemetry=telemetry)
    appender = providers.Factory(
        Appender,
        archive=storage.chronicle,
        state=storage.status,
        tail=storage.latest,
        planner=planner,
        mapper=storage.mapper,
        limit=core.settings.provided.historylimit,
        telemetry=telemetry,
    )
    swapper = providers.Factory(
        Swapper,
        archive=storage.chronicle,
        state=storage.status,
        tail=storage.latest,
        planner=planner,
        mapper=storage.mapper,
        limit=core.settings.provided.historylimit,
        telemetry=telemetry,
    )
    rewinder = providers.Factory(
        Rewinder,
        ledger=storage.chronicle,
        status=storage.status,
        restorer=restorer,
        planner=planner,
        latest=storage.latest,
        telemetry=telemetry,
    )
    setter = providers.Factory(
        Setter,
        ledger=storage.chronicle,
        status=storage.status,
        gateway=view.gateway,
        restorer=restorer,
        planner=planner,
        latest=storage.latest,
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
    alarm = providers.Factory(Alarm, gateway=view.gateway, alert=core.alert, telemetry=telemetry)


__all__ = ["UseCaseContainer"]

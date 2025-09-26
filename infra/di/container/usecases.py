from __future__ import annotations

from dataclasses import dataclass
from typing import Callable

from dependency_injector import containers, providers

from navigator.app.internal.policy import shield as inline_shield
from navigator.app.service import TailHistoryAccess, TailHistoryMutator
from navigator.app.service.navigator_runtime import NavigatorUseCases
from navigator.app.service.view.planner import (
    InlineRenderPlanner,
    RegularRenderPlanner,
    RenderPreparer,
    RenderSynchronizer,
    TailOperations,
    ViewPlanner,
)
from navigator.app.service.view.policy import adapt as adapt_payload
from navigator.app.service.view.restorer import ViewRestorer
from navigator.app.usecase.add import Appender
from navigator.app.usecase.alarm import Alarm
from navigator.app.usecase.back import Rewinder
from navigator.app.usecase.back_access import (
    RewindFinalizer,
    RewindHistoryReader,
    RewindHistoryWriter,
    RewindMutator,
    RewindRenderer,
)
from navigator.app.usecase.last import Tailer
from navigator.app.usecase.last.context import TailDecisionService, TailTelemetry
from navigator.app.usecase.last.inline import InlineEditCoordinator
from navigator.app.usecase.last.mutation import MessageEditCoordinator
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


@dataclass(frozen=True)
class NavigatorUsecaseProvider:
    """Factory interface exposing navigator use case bundles."""

    _appender: Callable[[], Appender]
    _swapper: Callable[[], Swapper]
    _rewinder: Callable[[], Rewinder]
    _setter: Callable[[], Setter]
    _trimmer: Callable[[], Trimmer]
    _shifter: Callable[[], Shifter]
    _tailer: Callable[[], Tailer]
    _alarm: Callable[[], Alarm]

    def navigator(self) -> NavigatorUseCases:
        return NavigatorUseCases(
            appender=self._appender(),
            swapper=self._swapper(),
            rewinder=self._rewinder(),
            setter=self._setter(),
            trimmer=self._trimmer(),
            shifter=self._shifter(),
            tailer=self._tailer(),
            alarm=self._alarm(),
        )


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
    tail_operations = providers.Factory(
        TailOperations,
        executor=view.executor,
        rendering=core.rendering,
    )
    inline_planner = providers.Factory(InlineRenderPlanner, synchronizer=render_synchronizer)
    regular_planner = providers.Factory(
        RegularRenderPlanner,
        album=view.album,
        synchronizer=render_synchronizer,
        tails=tail_operations,
        telemetry=telemetry,
    )
    render_preparer = providers.Factory(
        RenderPreparer,
        adapter=adapt_payload,
        shielder=inline_shield,
    )
    planner = providers.Factory(
        ViewPlanner,
        inline=inline_planner,
        regular=regular_planner,
        preparer=render_preparer,
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
    replace_history = providers.Factory(
        ReplaceHistoryAccess,
        archive=storage.chronicle,
        state=storage.status,
        telemetry=telemetry,
    )
    replace_preparation = providers.Factory(
        ReplacePreparation,
        planner=planner,
        mapper=storage.mapper,
    )
    replace_writer = providers.Factory(
        ReplaceHistoryWriter,
        archive=storage.chronicle,
        tail=storage.latest,
        limit=core.settings.provided.historylimit,
        telemetry=telemetry,
    )
    swapper = providers.Factory(
        Swapper,
        history=replace_history,
        preparation=replace_preparation,
        writer=replace_writer,
        telemetry=telemetry,
    )
    rewind_reader = providers.Factory(
        RewindHistoryReader,
        ledger=storage.chronicle,
        status=storage.status,
        telemetry=telemetry,
    )
    rewind_writer = providers.Factory(
        RewindHistoryWriter,
        ledger=storage.chronicle,
        status=storage.status,
        latest=storage.latest,
        telemetry=telemetry,
    )
    rewind_renderer = providers.Factory(
        RewindRenderer,
        restorer=restorer,
        planner=planner,
    )
    rewind_mutator = providers.Factory(RewindMutator)
    rewind_finalizer = providers.Factory(
        RewindFinalizer,
        writer=rewind_writer,
        mutator=rewind_mutator,
        telemetry=telemetry,
    )
    rewinder = providers.Factory(
        Rewinder,
        history=rewind_reader,
        writer=rewind_writer,
        renderer=rewind_renderer,
        mutator=rewind_mutator,
        finalizer=rewind_finalizer,
        telemetry=telemetry,
    )
    state_sync = providers.Factory(StateSynchronizer, state=storage.status, telemetry=telemetry)
    restoration_planner = providers.Factory(
        HistoryRestorationPlanner,
        ledger=storage.chronicle,
        telemetry=telemetry,
    )
    payload_reviver = providers.Factory(
        PayloadReviver,
        synchronizer=state_sync,
        restorer=restorer,
    )
    history_reconciler = providers.Factory(
        HistoryReconciler,
        ledger=storage.chronicle,
        latest=storage.latest,
        telemetry=telemetry,
    )
    setter = providers.Factory(
        Setter,
        planner=restoration_planner,
        state=state_sync,
        reviver=payload_reviver,
        renderer=planner,
        reconciler=history_reconciler,
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
    navigator = providers.Factory(
        NavigatorUsecaseProvider,
        _appender=appender,
        _swapper=swapper,
        _rewinder=rewinder,
        _setter=setter,
        _trimmer=trimmer,
        _shifter=shifter,
        _tailer=tailer,
        _alarm=alarm,
    )


__all__ = ["UseCaseContainer"]

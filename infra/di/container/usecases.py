from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.service.view.planner import ViewPlanner
from navigator.app.service.view.restorer import ViewRestorer
from navigator.app.usecase.add import Appender
from navigator.app.usecase.alarm import Alarm
from navigator.app.usecase.back import Rewinder
from navigator.app.usecase.last import Tailer
from navigator.app.usecase.pop import Trimmer
from navigator.app.usecase.rebase import Shifter
from navigator.app.usecase.replace import Swapper
from navigator.app.usecase.set import Setter


class UseCaseContainer(containers.DeclarativeContainer):
    core = providers.DependenciesContainer()
    storage = providers.DependenciesContainer()
    telegram = providers.DependenciesContainer()

    planner = providers.Factory(
        ViewPlanner,
        executor=telegram.executor,
        inline=telegram.inline,
        album=telegram.album,
        rendering=core.rendering,
    )
    restorer = providers.Factory(ViewRestorer, ledger=core.ledger)
    appender = providers.Factory(
        Appender,
        archive=storage.chronicle,
        state=storage.status,
        tail=storage.latest,
        planner=planner,
        mapper=storage.mapper,
        limit=core.settings.provided.history_limit,
    )
    swapper = providers.Factory(
        Swapper,
        archive=storage.chronicle,
        state=storage.status,
        tail=storage.latest,
        planner=planner,
        mapper=storage.mapper,
        limit=core.settings.provided.history_limit,
    )
    rewinder = providers.Factory(
        Rewinder,
        ledger=storage.chronicle,
        status=storage.status,
        gateway=telegram.gateway,
        restorer=restorer,
        planner=planner,
        latest=storage.latest,
    )
    setter = providers.Factory(
        Setter,
        ledger=storage.chronicle,
        status=storage.status,
        gateway=telegram.gateway,
        restorer=restorer,
        planner=planner,
        latest=storage.latest,
    )
    trimmer = providers.Factory(Trimmer, ledger=storage.chronicle, latest=storage.latest)
    shifter = providers.Factory(Shifter, ledger=storage.chronicle, latest=storage.latest)
    tailer = providers.Factory(
        Tailer,
        latest=storage.latest,
        ledger=storage.chronicle,
        planner=planner,
        executor=telegram.executor,
        inline=telegram.inline,
        rendering=core.rendering,
    )
    alarm = providers.Factory(Alarm, gateway=telegram.gateway, alert=core.alert)


__all__ = ["UseCaseContainer"]

from __future__ import annotations

from dependency_injector import containers, providers

from ...application.service.view.planner import ViewPlanner
from ...application.service.view.restorer import ViewRestorer
from ...application.usecase.add import Appender
from ...application.usecase.alarm import Alarm
from ...application.usecase.back import Rewinder
from ...application.usecase.last import Tailer
from ...application.usecase.pop import Trimmer
from ...application.usecase.rebase import Shifter
from ...application.usecase.replace import Swapper
from ...application.usecase.set import Setter


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

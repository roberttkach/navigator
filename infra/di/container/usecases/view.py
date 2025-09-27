"""Container wiring view-related helpers for navigator use cases."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.internal.policy import shield as inline_shield
from navigator.app.service.view.planner import (
    HeadAlignment,
    InlineRenderPlanner,
    RegularRenderPlanner,
    RenderPreparer,
    RenderSynchronizer,
    TailOperations,
    ViewPlanner,
)
from navigator.app.service.view.policy import adapt as adapt_payload
from navigator.app.service.view.restorer import ViewRestorer
from navigator.core.telemetry import Telemetry


class ViewRenderPlanningContainer(containers.DeclarativeContainer):
    """Compose planner related helpers for rendering flows."""

    core = providers.DependenciesContainer()
    view = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    executor = providers.Delegate(view.executor)
    inline = providers.Delegate(view.inline)
    album = providers.Delegate(view.album)

    render_synchronizer = providers.Factory(
        RenderSynchronizer,
        executor=executor,
        inline=inline,
        rendering=core.rendering,
    )
    tail_operations = providers.Factory(
        TailOperations,
        executor=executor,
        rendering=core.rendering,
    )
    inline_planner = providers.Factory(InlineRenderPlanner, synchronizer=render_synchronizer)
    head_alignment = providers.Factory(HeadAlignment, album=album, telemetry=telemetry)
    regular_planner = providers.Factory(
        RegularRenderPlanner,
        head=head_alignment,
        synchronizer=render_synchronizer,
        tails=tail_operations,
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


class ViewRestorationContainer(containers.DeclarativeContainer):
    """Isolate view restoration responsibilities."""

    core = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    restorer = providers.Factory(ViewRestorer, ledger=core.ledger, telemetry=telemetry)


class ViewSupportContainer(containers.DeclarativeContainer):
    """Expose reusable view planning helpers for navigator use cases."""

    core = providers.DependenciesContainer()
    view = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    gateway = providers.Delegate(view.gateway)

    planning = providers.Container(
        ViewRenderPlanningContainer,
        core=core,
        view=view,
        telemetry=telemetry,
    )
    restoration = providers.Container(
        ViewRestorationContainer,
        core=core,
        telemetry=telemetry,
    )

    executor = planning.provided.executor
    inline = planning.provided.inline
    album = planning.provided.album
    render_synchronizer = planning.provided.render_synchronizer
    tail_operations = planning.provided.tail_operations
    inline_planner = planning.provided.inline_planner
    head_alignment = planning.provided.head_alignment
    regular_planner = planning.provided.regular_planner
    render_preparer = planning.provided.render_preparer
    planner = planning.provided.planner
    restorer = restoration.provided.restorer


__all__ = ["ViewSupportContainer"]

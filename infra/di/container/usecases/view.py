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


class ViewSupportContainer(containers.DeclarativeContainer):
    """Expose reusable view planning helpers for navigator use cases."""

    core = providers.DependenciesContainer()
    view = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    gateway = providers.Delegate(view.gateway)
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
    restorer = providers.Factory(ViewRestorer, ledger=core.ledger, telemetry=telemetry)


__all__ = ["ViewSupportContainer"]

"""Container assembling state (set) history use case collaborators."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.usecase.set import Setter
from navigator.app.usecase.set_components import (
    HistoryReconciler,
    HistoryRestorationPlanner,
    PayloadReviver,
    StateSynchronizer,
)
from navigator.core.telemetry import Telemetry


class StateUseCaseContainer(containers.DeclarativeContainer):
    """Compose setter-related collaborators behind a focused container."""

    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)
    view_support = providers.DependenciesContainer()

    synchronizer = providers.Factory(StateSynchronizer, state=storage.status, telemetry=telemetry)
    planner = providers.Factory(
        HistoryRestorationPlanner,
        ledger=storage.chronicle,
        telemetry=telemetry,
    )
    reviver = providers.Factory(
        PayloadReviver,
        synchronizer=synchronizer,
        restorer=view_support.restorer,
    )
    reconciler = providers.Factory(
        HistoryReconciler.from_components,
        ledger=storage.chronicle,
        latest=storage.latest,
        telemetry=telemetry,
    )
    setter = providers.Factory(
        Setter,
        planner=planner,
        state=synchronizer,
        reviver=reviver,
        renderer=view_support.planner,
        reconciler=reconciler,
        telemetry=telemetry,
    )


__all__ = ["StateUseCaseContainer"]

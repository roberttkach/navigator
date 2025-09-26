"""Container grouping history maintenance (trim/rebase) use cases."""
from __future__ import annotations

from dependency_injector import containers, providers

from navigator.app.usecase.pop import Trimmer
from navigator.app.usecase.pop_instrumentation import PopInstrumentation
from navigator.app.usecase.rebase import Shifter
from navigator.app.usecase.rebase_instrumentation import RebaseInstrumentation
from navigator.core.telemetry import Telemetry


class MaintenanceUseCaseContainer(containers.DeclarativeContainer):
    """Provide history maintenance helpers (trim and shift)."""

    storage = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    pop_instrumentation = providers.Factory(
        PopInstrumentation,
        telemetry=telemetry,
    )
    trimmer = providers.Factory(
        Trimmer,
        ledger=storage.chronicle,
        latest=storage.latest,
        instrumentation=pop_instrumentation,
    )
    rebase_instrumentation = providers.Factory(
        RebaseInstrumentation,
        telemetry=telemetry,
    )
    shifter = providers.Factory(
        Shifter,
        ledger=storage.chronicle,
        latest=storage.latest,
        instrumentation=rebase_instrumentation,
    )


__all__ = ["MaintenanceUseCaseContainer"]

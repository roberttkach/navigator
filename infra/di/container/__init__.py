"""Application dependency injection container."""
from __future__ import annotations

from dataclasses import dataclass

from dependency_injector import containers, providers

from navigator.adapters.storage.fsm.context import StateContext
from navigator.core.port.factory import ViewLedger
from navigator.app.service.navigator_runtime.snapshot import (
    NavigatorRuntimeSnapshot,
)
from navigator.core.telemetry import Telemetry

from .core import CoreContainer
from .runtime import NavigatorRuntimeContainer
from .storage import StorageContainer
from .usecases import UseCaseContainer
from .usecases.view import ViewSupportContainer


class CoreBindings(containers.DeclarativeContainer):
    """Expose base dependencies shared across modules."""

    event = providers.Dependency()
    state = providers.Dependency(instance_of=StateContext)
    ledger = providers.Dependency(instance_of=ViewLedger)
    alert = providers.Dependency()
    telemetry = providers.Dependency(instance_of=Telemetry)

    core = providers.Container(
        CoreContainer,
        event=event,
        state=state,
        ledger=ledger,
        alert=alert,
        telemetry=telemetry,
    )


class IntegrationBindings(containers.DeclarativeContainer):
    """Configure infrastructure and presentation integration containers."""

    core = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)
    view_container = providers.Dependency()

    storage = providers.Container(
        StorageContainer,
        core=core.provided.core,
        telemetry=telemetry,
    )
    view = providers.Container(
        view_container,
        core=core.provided.core,
        telemetry=telemetry,
    )
    view_support = providers.Container(
        ViewSupportContainer,
        core=core.provided.core,
        view=view,
        telemetry=telemetry,
    )


class UseCaseBindings(containers.DeclarativeContainer):
    """Compose use case providers without touching infrastructure details."""

    core = providers.DependenciesContainer()
    integration = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    usecases = providers.Container(
        UseCaseContainer,
        core=core.provided.core,
        storage=integration.provided.storage,
        view_support=integration.provided.view_support,
        telemetry=telemetry,
    )


class RuntimeBindings(containers.DeclarativeContainer):
    """Group runtime-specific wiring behind a dedicated binding container."""

    core = providers.DependenciesContainer()
    usecases = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    runtime = providers.Container(
        NavigatorRuntimeContainer,
        core=core.provided.core,
        usecases=usecases.provided.usecases,
        telemetry=telemetry,
    )


@dataclass(slots=True)
class AppContainer:
    """Aggregate binding containers without exposing infrastructure details."""

    core: CoreBindings
    integration: IntegrationBindings
    usecases: UseCaseBindings
    runtime_bindings: RuntimeBindings

    def runtime(self) -> NavigatorRuntimeContainer:
        """Expose runtime bindings produced by the application composition root."""

        return self.runtime_bindings.runtime()

    def snapshot(self) -> NavigatorRuntimeSnapshot:
        """Return the runtime snapshot without exposing container internals."""

        runtime = self.runtime()
        return runtime.snapshot()


__all__ = [
    "AppContainer",
    "CoreBindings",
    "IntegrationBindings",
    "RuntimeBindings",
    "UseCaseBindings",
]

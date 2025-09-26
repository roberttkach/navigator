"""Application dependency injection container."""
from __future__ import annotations

from dependency_injector import containers, providers
from aiogram.fsm.context import FSMContext
from navigator.core.port.factory import ViewLedger
from navigator.core.telemetry import Telemetry

from .core import CoreContainer
from .runtime import NavigatorRuntimeContainer
from .storage import StorageContainer
from .usecases import UseCaseContainer
from .usecases.view import ViewSupportContainer


class CoreBindings(containers.DeclarativeContainer):
    """Expose base dependencies shared across modules."""

    event = providers.Dependency()
    state = providers.Dependency(instance_of=FSMContext)
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


class AppContainer(containers.DeclarativeContainer):
    """High-level composition root that delegates to dedicated bindings."""

    event = providers.Dependency()
    state = providers.Dependency(instance_of=FSMContext)
    ledger = providers.Dependency(instance_of=ViewLedger)
    alert = providers.Dependency()
    telemetry = providers.Dependency(instance_of=Telemetry)
    view_container = providers.Dependency()

    _core = providers.Container(
        CoreBindings,
        event=event,
        state=state,
        ledger=ledger,
        alert=alert,
        telemetry=telemetry,
    )
    _integration = providers.Container(
        IntegrationBindings,
        core=_core,
        telemetry=telemetry,
        view_container=view_container,
    )
    _usecase = providers.Container(
        UseCaseBindings,
        core=_core,
        integration=_integration,
        telemetry=telemetry,
    )
    _runtime = providers.Container(
        RuntimeBindings,
        core=_core,
        usecases=_usecase,
        telemetry=telemetry,
    )

    runtime = providers.Delegate(_runtime.provided.runtime)


__all__ = [
    "AppContainer",
    "CoreBindings",
    "IntegrationBindings",
    "RuntimeBindings",
    "UseCaseBindings",
]

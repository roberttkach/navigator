"""Bindings wiring infrastructure integrations for the application container."""

from __future__ import annotations

from dependency_injector import containers, providers

from navigator.core.telemetry import Telemetry

from ..storage import StorageContainer
from ..usecases.view import ViewSupportContainer


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


__all__ = ["IntegrationBindings"]

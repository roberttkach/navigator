"""Bindings exposing application use cases to runtime layers."""

from __future__ import annotations

from dependency_injector import containers, providers

from navigator.core.telemetry import Telemetry

from ..usecases import UseCaseContainer


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


__all__ = ["UseCaseBindings"]

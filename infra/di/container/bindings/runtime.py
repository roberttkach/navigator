"""Bindings configuring navigator runtime specific providers."""

from __future__ import annotations

from dependency_injector import containers, providers

from navigator.core.telemetry import Telemetry

from ..runtime import NavigatorRuntimeContainer


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


__all__ = ["RuntimeBindings"]

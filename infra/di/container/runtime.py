"""Navigator runtime specific container helpers."""

from __future__ import annotations

from dependency_injector import containers, providers

from navigator.core.telemetry import Telemetry
from navigator.app.service.navigator_runtime.dependencies import (
    RuntimeDomainServices,
    RuntimeSafetyServices,
    RuntimeTelemetryServices,
)
from navigator.app.service.navigator_runtime.snapshot import NavigatorRuntimeSnapshot
from navigator.infra.config.redaction import RuntimeRedactionConfig


class NavigatorRuntimeContainer(containers.DeclarativeContainer):
    """Expose navigator runtime dependencies via dedicated providers."""

    core = providers.DependenciesContainer()
    usecases = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    domain_services = providers.Factory(
        RuntimeDomainServices,
        usecases=usecases.provided.navigator,
    )

    telemetry_services = providers.Factory(
        RuntimeTelemetryServices,
        telemetry=telemetry,
    )

    safety_services = providers.Factory(
        RuntimeSafetyServices,
        guard=core.provided.guard,
        missing_alert=core.alert,
    )

    redaction = providers.Factory(
        RuntimeRedactionConfig.from_settings,
        settings=core.provided.settings,
    )

    snapshot = providers.Factory(
        NavigatorRuntimeSnapshot,
        domain=domain_services,
        telemetry=telemetry_services,
        safety=safety_services,
        redaction=redaction.provided.value,
    )


__all__ = ["NavigatorRuntimeContainer"]

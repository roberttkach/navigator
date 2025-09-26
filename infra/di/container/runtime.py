"""Navigator runtime specific container helpers."""

from __future__ import annotations

from dependency_injector import containers, providers

from navigator.core.telemetry import Telemetry
from navigator.app.service.navigator_runtime.dependencies import NavigatorDependencies


class NavigatorRuntimeContainer(containers.DeclarativeContainer):
    """Expose navigator runtime dependencies via dedicated providers."""

    core = providers.DependenciesContainer()
    usecases = providers.DependenciesContainer()
    telemetry = providers.Dependency(instance_of=Telemetry)

    dependencies = providers.Factory(
        NavigatorDependencies,
        usecases=usecases.provided.navigator,
        guard=core.provided.guard,
        telemetry=telemetry,
        missing_alert=core.alert,
    )

    redaction = providers.Callable(
        lambda settings: getattr(settings, "redaction", ""),
        core.provided.settings,
    )


__all__ = ["NavigatorRuntimeContainer"]


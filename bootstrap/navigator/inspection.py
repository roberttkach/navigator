"""Helpers for extracting navigator runtime dependencies from the DI container."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.service.navigator_runtime import MissingAlert
from navigator.core.telemetry import Telemetry
from navigator.infra.di.container import AppContainer
from navigator.presentation.bootstrap.navigator import NavigatorDependencies


@dataclass(frozen=True)
class NavigatorContainerSnapshot:
    """Immutable view of services exposed by the application container."""

    dependencies: NavigatorDependencies
    redaction: str


def inspect_container(container: AppContainer) -> NavigatorContainerSnapshot:
    """Collect runtime dependencies and configuration from the container."""

    core = container.core()
    telemetry: Telemetry = core.telemetry()
    guard = core.guard()
    alert: MissingAlert = core.alert()
    settings = core.settings()
    usecases = container.usecases().navigator()
    dependencies = NavigatorDependencies(
        usecases=usecases,
        guard=guard,
        telemetry=telemetry,
        missing_alert=alert,
    )
    return NavigatorContainerSnapshot(
        dependencies=dependencies,
        redaction=getattr(settings, "redaction", ""),
    )


__all__ = ["NavigatorContainerSnapshot", "inspect_container"]

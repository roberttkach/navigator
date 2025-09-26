"""Helpers for extracting navigator runtime dependencies from the DI container."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.service.navigator_runtime.dependencies import NavigatorDependencies
from navigator.infra.di.container import AppContainer


@dataclass(frozen=True)
class NavigatorContainerSnapshot:
    """Immutable view of services exposed by the application container."""

    dependencies: NavigatorDependencies
    redaction: str


def inspect_container(container: AppContainer) -> NavigatorContainerSnapshot:
    """Collect runtime dependencies and configuration from the container."""

    runtime = container.runtime()
    dependencies = runtime.dependencies()
    return NavigatorContainerSnapshot(
        dependencies=dependencies,
        redaction=runtime.redaction(),
    )


__all__ = ["NavigatorContainerSnapshot", "inspect_container"]

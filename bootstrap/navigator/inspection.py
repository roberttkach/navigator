"""Helpers for extracting navigator runtime dependencies from the DI container."""
from __future__ import annotations

from navigator.app.service.navigator_runtime.snapshot import NavigatorRuntimeSnapshot
from navigator.infra.di.container import AppContainer


def inspect_container(container: AppContainer) -> NavigatorRuntimeSnapshot:
    """Collect runtime dependencies and configuration from the container."""

    runtime = container.runtime()
    return runtime.snapshot()


__all__ = ["inspect_container"]

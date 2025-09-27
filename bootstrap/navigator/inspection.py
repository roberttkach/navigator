"""Helpers for extracting navigator runtime dependencies from the DI container."""
from __future__ import annotations

from navigator.app.service.navigator_runtime.snapshot import NavigatorRuntimeSnapshot

from .container_types import RuntimeContainer


def inspect_container(container: RuntimeContainer) -> NavigatorRuntimeSnapshot:
    """Collect runtime dependencies and configuration from the container."""

    return container.snapshot()


__all__ = ["inspect_container"]

"""Runtime factory helpers for presentation bootstrap."""

from __future__ import annotations

from typing import Protocol

from navigator.app.locks.guard import Guardian
from navigator.app.service.navigator_runtime import build_runtime_from_dependencies
from navigator.app.service.navigator_runtime.runtime import NavigatorRuntime
from navigator.app.service.navigator_runtime.snapshot import NavigatorRuntimeSnapshot
from navigator.core.contracts import MissingAlert
from navigator.core.value.message import Scope


class NavigatorRuntimeFactory(Protocol):
    """Protocol describing runtime factory callables used by bootstrap."""

    def __call__(
        self,
        dependencies: NavigatorRuntimeSnapshot,
        scope: Scope,
        *,
        guard: Guardian | None = None,
        missing_alert: MissingAlert | None = None,
    ) -> NavigatorRuntime:
        """Return a navigator runtime configured for presentation."""


def default_runtime_factory() -> NavigatorRuntimeFactory:
    """Return the default runtime factory backed by the application service."""

    def _factory(
        dependencies: NavigatorRuntimeSnapshot,
        scope: Scope,
        *,
        guard: Guardian | None = None,
        missing_alert: MissingAlert | None = None,
    ) -> NavigatorRuntime:
        return build_runtime_from_dependencies(
            dependencies,
            scope,
            guard=guard,
            missing_alert=missing_alert,
        )

    return _factory


__all__ = ["NavigatorRuntimeFactory", "default_runtime_factory"]

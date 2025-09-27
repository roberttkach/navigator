"""Navigator composer responsible for building navigator runtimes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, TYPE_CHECKING

from navigator.app.locks.guard import Guardian
from navigator.core.contracts import MissingAlert
from navigator.core.value.message import Scope
from navigator.presentation.navigator import Navigator

from .runtime_gateway import NavigatorRuntimePort, RuntimeRequest

if TYPE_CHECKING:
    from navigator.app.service.navigator_runtime.snapshot import NavigatorRuntimeSnapshot
    from navigator.app.service.navigator_runtime.runtime import NavigatorRuntime
else:  # pragma: no cover - runtime typing fallback
    NavigatorRuntimeSnapshot = Any
    NavigatorRuntime = Any


@dataclass(frozen=True)
class NavigatorComposer:
    """Compose navigators using an injected runtime factory."""

    runtime_port: NavigatorRuntimePort

    def build_runtime(
        self,
        dependencies: NavigatorRuntimeSnapshot,
        scope: Scope,
        *,
        guard: Guardian | None = None,
        missing_alert: MissingAlert | None = None,
    ) -> NavigatorRuntime:
        request = RuntimeRequest(scope=scope, guard=guard, missing_alert=missing_alert)
        return self.runtime_port.create_runtime(dependencies, request)

    def compose(
        self,
        dependencies: NavigatorRuntimeSnapshot,
        scope: Scope,
        *,
        guard: Guardian | None = None,
        missing_alert: MissingAlert | None = None,
    ) -> Navigator:
        runtime = self.build_runtime(
            dependencies,
            scope,
            guard=guard,
            missing_alert=missing_alert,
        )
        return Navigator(runtime)


__all__ = ["NavigatorComposer", "NavigatorRuntimeSnapshot", "NavigatorRuntime"]

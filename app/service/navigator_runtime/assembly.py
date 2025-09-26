"""High level helpers to build navigator runtime instances."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope

from .builder import build_navigator_runtime
from .dependencies import NavigatorDependencies
from .runtime import NavigatorRuntime
from .types import MissingAlert


def build_runtime_from_dependencies(
    dependencies: NavigatorDependencies,
    scope: Scope,
    *,
    guard: Guardian | None = None,
    missing_alert: MissingAlert | None = None,
) -> NavigatorRuntime:
    """Compose a :class:`NavigatorRuntime` from resolved dependencies."""

    return build_navigator_runtime(
        usecases=dependencies.usecases,
        scope=scope,
        guard=guard or dependencies.guard,
        telemetry=dependencies.telemetry,
        missing_alert=missing_alert or dependencies.missing_alert,
    )


__all__ = ["build_runtime_from_dependencies"]

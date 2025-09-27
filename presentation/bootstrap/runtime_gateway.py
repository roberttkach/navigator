"""Presentation-facing gateway for building navigator runtimes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Protocol, TYPE_CHECKING

from navigator.app.locks.guard import Guardian
from navigator.core.contracts import MissingAlert
from navigator.core.value.message import Scope

from .runtime_factory import NavigatorRuntimeFactory, default_runtime_factory

if TYPE_CHECKING:
    from navigator.app.service.navigator_runtime.dependencies import NavigatorDependencies
    from navigator.app.service.navigator_runtime.runtime import NavigatorRuntime
else:  # pragma: no cover - runtime typing fallback
    NavigatorDependencies = Any
    NavigatorRuntime = Any


@dataclass(frozen=True)
class RuntimeRequest:
    """Capture the information required to provision a runtime instance."""

    scope: Scope
    guard: Guardian | None = None
    missing_alert: MissingAlert | None = None


class NavigatorRuntimePort(Protocol):
    """Protocol abstracting runtime construction for presentation layer."""

    def create_runtime(
        self,
        dependencies: NavigatorDependencies,
        request: RuntimeRequest,
    ) -> NavigatorRuntime:
        """Provision a runtime using resolved dependencies and request metadata."""


class _FactoryRuntimePort:
    """Default implementation backed by an application runtime factory."""

    def __init__(self, factory: NavigatorRuntimeFactory) -> None:
        self._factory = factory

    def create_runtime(
        self,
        dependencies: NavigatorDependencies,
        request: RuntimeRequest,
    ) -> NavigatorRuntime:
        return self._factory(
            dependencies,
            request.scope,
            guard=request.guard,
            missing_alert=request.missing_alert,
        )


def default_runtime_port() -> NavigatorRuntimePort:
    """Return a runtime port backed by the default application factory."""

    return _FactoryRuntimePort(default_runtime_factory())


__all__ = [
    "NavigatorRuntimePort",
    "RuntimeRequest",
    "default_runtime_port",
]

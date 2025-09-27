"""Collaborator planning helpers for runtime plan construction."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from navigator.core.value.message import Scope

from ..bundler import PayloadBundler
from ..runtime_collaborator_factory import RuntimeCollaboratorFactory
from ..runtime_inputs import RuntimeCollaboratorRequest
from ..runtime_plan_dependencies import (
    RuntimeInstrumentationDependencies,
    RuntimeNotificationDependencies,
)


@dataclass(frozen=True)
class RuntimeCollaboratorPlanner:
    """Create collaborator requests for runtime plans."""

    factory: RuntimeCollaboratorFactory

    @classmethod
    def create_default(cls) -> "RuntimeCollaboratorPlanner":
        return cls(RuntimeCollaboratorFactory())

    def request(
        self,
        *,
        scope: Scope,
        instrumentation: RuntimeInstrumentationDependencies | None = None,
        notifications: RuntimeNotificationDependencies | None = None,
        bundler: PayloadBundler | None = None,
    ) -> RuntimeCollaboratorRequest:
        return self.factory.create(
            scope=scope,
            instrumentation=instrumentation,
            notifications=notifications,
            bundler=bundler,
        )


class CollaboratorPlanning(Protocol):
    """Expose collaborator request capabilities without leaking implementation."""

    def request(
        self,
        *,
        scope: Scope,
        instrumentation: RuntimeInstrumentationDependencies | None = None,
        notifications: RuntimeNotificationDependencies | None = None,
        bundler: PayloadBundler | None = None,
    ) -> RuntimeCollaboratorRequest:
        ...


def build_runtime_collaborators(
    *,
    scope: Scope,
    instrumentation: RuntimeInstrumentationDependencies | None = None,
    notifications: RuntimeNotificationDependencies | None = None,
    bundler: PayloadBundler | None = None,
    planner: CollaboratorPlanning | None = None,
) -> RuntimeCollaboratorRequest:
    """Create the collaborator request for a runtime plan."""

    candidate = planner or RuntimeCollaboratorPlanner.create_default()
    return candidate.request(
        scope=scope,
        instrumentation=instrumentation,
        notifications=notifications,
        bundler=bundler,
    )


__all__ = [
    "CollaboratorPlanning",
    "RuntimeCollaboratorPlanner",
    "build_runtime_collaborators",
]

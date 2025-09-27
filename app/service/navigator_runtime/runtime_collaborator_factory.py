"""Factories responsible for creating runtime collaborator requests."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .runtime_inputs import RuntimeCollaboratorRequest
from .runtime_plan_dependencies import (
    RuntimeInstrumentationDependencies,
    RuntimeNotificationDependencies,
)


@dataclass(frozen=True)
class RuntimeCollaboratorFactory:
    """Create collaborator requests decoupled from request orchestration."""

    def create(
        self,
        *,
        scope: Scope,
        instrumentation: RuntimeInstrumentationDependencies | None = None,
        notifications: RuntimeNotificationDependencies | None = None,
        bundler: PayloadBundler | None = None,
    ) -> RuntimeCollaboratorRequest:
        """Return a collaborator request describing runtime auxiliaries."""

        instrumentation = instrumentation or RuntimeInstrumentationDependencies()
        notifications = notifications or RuntimeNotificationDependencies()
        return RuntimeCollaboratorRequest(
            scope=scope,
            telemetry=instrumentation.telemetry,
            reporter=notifications.reporter,
            bundler=bundler,
            tail_telemetry=instrumentation.tail,
            missing_alert=notifications.missing_alert,
        )


__all__ = ["RuntimeCollaboratorFactory"]

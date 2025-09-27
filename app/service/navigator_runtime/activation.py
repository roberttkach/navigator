"""Activation plans translating snapshots into runnable runtimes."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from navigator.core.value.message import Scope

from .dependencies import RuntimeDomainServices, RuntimeSafetyServices, RuntimeTelemetryServices
from .runtime_factory import (
    NavigatorRuntimeAssembly,
    build_navigator_runtime,
    build_runtime_collaborators,
    build_runtime_contract_selection,
    RuntimePlanRequest,
)
from .runtime import NavigatorRuntime

if TYPE_CHECKING:
    from navigator.app.locks.guard import Guardian

    from .snapshot import NavigatorRuntimeSnapshot
    from .types import MissingAlert


@dataclass(frozen=True)
class RuntimeActivationPlan:
    """Immutable description of how to activate the navigator runtime."""

    domain: RuntimeDomainServices
    telemetry: RuntimeTelemetryServices
    scope: Scope
    safety: RuntimeSafetyServices

    def activate(self) -> NavigatorRuntime:
        """Build a runtime instance according to the stored plan."""

        plan_request = self._create_plan_request()
        assembly = NavigatorRuntimeAssembly(guard=self.safety.guard, plan=plan_request)
        return build_navigator_runtime(assembly=assembly)

    def _create_plan_request(self) -> RuntimePlanRequest:
        """Compose the runtime plan request using dedicated builders."""

        contracts = build_runtime_contract_selection(usecases=self.domain.usecases)
        collaborators = build_runtime_collaborators(
            scope=self.scope,
            telemetry=self.telemetry.telemetry,
            missing_alert=self.safety.missing_alert,
        )
        return RuntimePlanRequest(contracts=contracts, collaborators=collaborators)


def create_activation_plan(
    snapshot: NavigatorRuntimeSnapshot,
    scope: Scope,
    *,
    guard: Guardian | None = None,
    missing_alert: MissingAlert | None = None,
) -> RuntimeActivationPlan:
    """Derive a runtime activation plan from container snapshot data."""

    return snapshot.create_activation_plan(
        scope,
        guard=guard,
        missing_alert=missing_alert,
    )


__all__ = ["RuntimeActivationPlan", "create_activation_plan"]

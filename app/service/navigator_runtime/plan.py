"""Activation plan primitives shared across navigator runtime services."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.value.message import Scope

from .dependencies import (
    RuntimeDomainServices,
    RuntimeSafetyServices,
    RuntimeTelemetryServices,
)
from .runtime import NavigatorRuntime
from .runtime_factory import (
    NavigatorRuntimeAssembly,
    RuntimeInstrumentationDependencies,
    RuntimeNotificationDependencies,
    RuntimePlanRequest,
    build_navigator_runtime,
    build_runtime_collaborators,
    build_runtime_contract_selection,
)


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
            instrumentation=RuntimeInstrumentationDependencies(
                telemetry=self.telemetry.telemetry,
            ),
            notifications=RuntimeNotificationDependencies(
                missing_alert=self.safety.missing_alert,
            ),
        )
        return RuntimePlanRequest(contracts=contracts, collaborators=collaborators)


__all__ = ["RuntimeActivationPlan"]

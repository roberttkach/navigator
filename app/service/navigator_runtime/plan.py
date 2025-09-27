"""Activation plan primitives shared across navigator runtime services."""
from __future__ import annotations

from dataclasses import dataclass, field

from navigator.core.value.message import Scope

from .dependencies import (
    RuntimeDomainServices,
    RuntimeSafetyServices,
    RuntimeTelemetryServices,
)
from .runtime import NavigatorRuntime
from .runtime_activation_builder import RuntimeActivationBuilder
from .runtime_plan import RuntimePlanRequest
from .runtime_plan_dependencies import (
    RuntimeInstrumentationDependencies,
    RuntimeNotificationDependencies,
)
from .runtime_planning import RuntimePlanRequestPlanner


@dataclass(frozen=True)
class RuntimePlanRequestFactory:
    """Create runtime plan requests from activation services."""

    planner: RuntimePlanRequestPlanner = field(
        default_factory=RuntimePlanRequestPlanner.create_default
    )

    def create(
        self,
        *,
        domain: RuntimeDomainServices,
        telemetry: RuntimeTelemetryServices,
        scope: Scope,
        safety: RuntimeSafetyServices,
    ) -> RuntimePlanRequest:
        instrumentation = RuntimeInstrumentationDependencies(
            telemetry=telemetry.telemetry,
        )
        notifications = RuntimeNotificationDependencies(
            missing_alert=safety.missing_alert,
        )
        return self.planner.build(
            scope=scope,
            usecases=domain.usecases,
            instrumentation=instrumentation,
            notifications=notifications,
        )


@dataclass(frozen=True)
class RuntimeActivationPlan:
    """Immutable description of how to activate the navigator runtime."""

    domain: RuntimeDomainServices
    telemetry: RuntimeTelemetryServices
    scope: Scope
    safety: RuntimeSafetyServices
    request_factory: RuntimePlanRequestFactory = field(default_factory=RuntimePlanRequestFactory)
    runtime_builder: RuntimeActivationBuilder = field(
        default_factory=RuntimeActivationBuilder
    )

    def activate(self) -> NavigatorRuntime:
        """Build a runtime instance according to the stored plan."""

        plan_request = self.request_factory.create(
            domain=self.domain,
            telemetry=self.telemetry,
            scope=self.scope,
            safety=self.safety,
        )
        return self.runtime_builder.build(
            guard=self.safety.guard,
            plan=plan_request,
        )


__all__ = ["RuntimeActivationPlan", "RuntimePlanRequestFactory"]

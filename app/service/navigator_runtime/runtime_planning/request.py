"""Runtime plan request planning helpers."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.value.message import Scope

from ..bundler import PayloadBundler
from ..contracts import NavigatorRuntimeContracts
from ..runtime_collaborator_factory import RuntimeCollaboratorFactory
from ..runtime_contract_selector import RuntimeContractSelector
from ..runtime_plan import RuntimePlanRequest
from ..runtime_plan_dependencies import (
    RuntimeInstrumentationDependencies,
    RuntimeNotificationDependencies,
)
from ..runtime_plan_request_builder import RuntimePlanRequestBuilder
from ..usecases import NavigatorUseCases


@dataclass(frozen=True)
class RuntimePlanRequestPlanner:
    """Assemble runtime plan requests from configured request builders."""

    builder: RuntimePlanRequestBuilder

    @classmethod
    def create_default(cls) -> "RuntimePlanRequestPlanner":
        builder = RuntimePlanRequestBuilder(
            contract_selector=RuntimeContractSelector(),
            collaborator_factory=RuntimeCollaboratorFactory(),
        )
        return cls(builder=builder)

    def build(
        self,
        *,
        scope: Scope,
        usecases: NavigatorUseCases | None = None,
        contracts: NavigatorRuntimeContracts | None = None,
        instrumentation: RuntimeInstrumentationDependencies | None = None,
        notifications: RuntimeNotificationDependencies | None = None,
        bundler: PayloadBundler | None = None,
    ) -> RuntimePlanRequest:
        return self.builder.build(
            scope=scope,
            usecases=usecases,
            contracts=contracts,
            instrumentation=instrumentation,
            notifications=notifications,
            bundler=bundler,
        )


def create_runtime_plan_request(
    *,
    scope: Scope,
    usecases: NavigatorUseCases | None = None,
    contracts: NavigatorRuntimeContracts | None = None,
    instrumentation: RuntimeInstrumentationDependencies | None = None,
    notifications: RuntimeNotificationDependencies | None = None,
    bundler: PayloadBundler | None = None,
    planner: RuntimePlanRequestPlanner | None = None,
) -> RuntimePlanRequest:
    """Build a runtime plan request aggregating domain and infrastructure inputs."""

    resolved_planner = planner or RuntimePlanRequestPlanner.create_default()
    return resolved_planner.build(
        scope=scope,
        usecases=usecases,
        contracts=contracts,
        instrumentation=instrumentation,
        notifications=notifications,
        bundler=bundler,
    )


__all__ = [
    "RuntimePlanRequestPlanner",
    "create_runtime_plan_request",
]

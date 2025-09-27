"""Factory helpers building the navigator runtime."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope

from .contracts import NavigatorRuntimeContracts, RuntimeContractSelection
from .runtime import NavigatorRuntime
from .runtime_assembler import NavigatorRuntimeAssembler
from .runtime_inputs import RuntimeCollaboratorRequest
from .runtime_plan import RuntimeAssemblyPlan, RuntimePlanRequest, create_runtime_plan
from .runtime_plan_request_builder import (
    RuntimeCollaboratorFactory,
    RuntimeContractSelector,
    RuntimePlanRequestBuilder,
    RuntimePlannerDependencies,
)
from .usecases import NavigatorUseCases


@dataclass(frozen=True)
class NavigatorRuntimeAssembly:
    """Capture the minimal context required to assemble the runtime."""

    guard: Guardian
    plan: RuntimePlanRequest

    @property
    def scope(self) -> Scope:
        """Expose scope associated with the runtime plan."""

        return self.plan.collaborators.scope


@dataclass(frozen=True)
class NavigatorRuntimePlanner:
    """Aggregate collaborators used to prepare runtime plans."""

    selector: RuntimeContractSelector
    collaborators: RuntimeCollaboratorFactory
    builder: RuntimePlanRequestBuilder

    @classmethod
    def create_default(cls) -> "NavigatorRuntimePlanner":
        selector = RuntimeContractSelector()
        collaborators = RuntimeCollaboratorFactory()
        builder = RuntimePlanRequestBuilder(
            contract_selector=selector,
            collaborator_factory=collaborators,
        )
        return cls(selector=selector, collaborators=collaborators, builder=builder)

    def select_contracts(
        self,
        *,
        usecases: NavigatorUseCases | None = None,
        contracts: NavigatorRuntimeContracts | None = None,
    ) -> RuntimeContractSelection:
        return self.selector.select(usecases=usecases, contracts=contracts)

    def collaborators_request(
        self,
        *,
        scope: Scope,
        dependencies: RuntimePlannerDependencies | None = None,
    ) -> RuntimeCollaboratorRequest:
        payload = dependencies or RuntimePlannerDependencies()
        return self.collaborators.create(scope=scope, dependencies=payload)

    def plan_request(
        self,
        *,
        scope: Scope,
        usecases: NavigatorUseCases | None = None,
        contracts: NavigatorRuntimeContracts | None = None,
        dependencies: RuntimePlannerDependencies | None = None,
    ) -> RuntimePlanRequest:
        payload = dependencies or RuntimePlannerDependencies()
        return self.builder.build(
            scope=scope,
            usecases=usecases,
            contracts=contracts,
            dependencies=payload,
        )


def _planner(planner: NavigatorRuntimePlanner | None) -> NavigatorRuntimePlanner:
    return planner or NavigatorRuntimePlanner.create_default()


def build_runtime_contract_selection(
    *,
    usecases: NavigatorUseCases | None = None,
    contracts: NavigatorRuntimeContracts | None = None,
    planner: NavigatorRuntimePlanner | None = None,
) -> RuntimeContractSelection:
    """Create the contract selection descriptor for a runtime plan."""

    return _planner(planner).select_contracts(
        usecases=usecases, contracts=contracts
    )


def build_runtime_collaborators(
    *,
    scope: Scope,
    dependencies: RuntimePlannerDependencies | None = None,
    planner: NavigatorRuntimePlanner | None = None,
) -> RuntimeCollaboratorRequest:
    """Create the collaborator request for a runtime plan."""

    return _planner(planner).collaborators_request(
        scope=scope,
        dependencies=dependencies,
    )


def create_runtime_plan_request(
    *,
    scope: Scope,
    usecases: NavigatorUseCases | None = None,
    contracts: NavigatorRuntimeContracts | None = None,
    dependencies: RuntimePlannerDependencies | None = None,
    planner: NavigatorRuntimePlanner | None = None,
) -> RuntimePlanRequest:
    """Build a runtime plan request aggregating domain and infrastructure inputs."""

    return _planner(planner).plan_request(
        scope=scope,
        usecases=usecases,
        contracts=contracts,
        dependencies=dependencies,
    )


def build_navigator_runtime(*, assembly: NavigatorRuntimeAssembly) -> NavigatorRuntime:
    """Create a navigator runtime wiring use cases with cross-cutting tools."""

    plan = create_runtime_plan(assembly.plan)
    assembler = NavigatorRuntimeAssembler.from_context(
        guard=assembly.guard, scope=assembly.scope
    )
    return assembler.assemble(plan)


__all__ = [
    "NavigatorRuntimeAssembly",
    "NavigatorRuntimePlanner",
    "RuntimeAssemblyPlan",
    "RuntimePlannerDependencies",
    "build_navigator_runtime",
    "build_runtime_collaborators",
    "build_runtime_contract_selection",
    "create_runtime_plan",
    "create_runtime_plan_request",
]

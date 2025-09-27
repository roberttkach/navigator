"""Factory helpers building the navigator runtime."""
from __future__ import annotations

from dataclasses import dataclass
from typing import overload

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
class RuntimeContractPlanner:
    """Prepare contract selections for runtime plans."""

    selector: RuntimeContractSelector

    @classmethod
    def create_default(cls) -> "RuntimeContractPlanner":
        return cls(RuntimeContractSelector())

    def select(
        self,
        *,
        usecases: NavigatorUseCases | None = None,
        contracts: NavigatorRuntimeContracts | None = None,
    ) -> RuntimeContractSelection:
        return self.selector.select(usecases=usecases, contracts=contracts)


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
        dependencies: RuntimePlannerDependencies | None = None,
    ) -> RuntimeCollaboratorRequest:
        payload = dependencies or RuntimePlannerDependencies()
        return self.factory.create(scope=scope, dependencies=payload)


@dataclass(frozen=True)
class RuntimePlanRequestPlanner:
    """Assemble runtime plan requests from individual planning steps."""

    builder: RuntimePlanRequestBuilder
    contracts: RuntimeContractPlanner
    collaborators: RuntimeCollaboratorPlanner

    @classmethod
    def create_default(cls) -> "RuntimePlanRequestPlanner":
        contract_planner = RuntimeContractPlanner.create_default()
        collaborator_planner = RuntimeCollaboratorPlanner.create_default()
        builder = RuntimePlanRequestBuilder(
            contract_selector=contract_planner.selector,
            collaborator_factory=collaborator_planner.factory,
        )
        return cls(
            builder=builder,
            contracts=contract_planner,
            collaborators=collaborator_planner,
        )

    def build(
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


@overload
def _contract_planner(
    planner: RuntimePlanRequestPlanner | None,
) -> RuntimeContractPlanner:
    ...


@overload
def _contract_planner(
    planner: RuntimeContractPlanner | None,
) -> RuntimeContractPlanner:
    ...


def _contract_planner(
    planner: RuntimeContractPlanner | RuntimePlanRequestPlanner | None,
) -> RuntimeContractPlanner:
    if planner is None:
        return RuntimeContractPlanner.create_default()
    if isinstance(planner, RuntimePlanRequestPlanner):
        return planner.contracts
    return planner


@overload
def _collaborator_planner(
    planner: RuntimePlanRequestPlanner | None,
) -> RuntimeCollaboratorPlanner:
    ...


@overload
def _collaborator_planner(
    planner: RuntimeCollaboratorPlanner | None,
) -> RuntimeCollaboratorPlanner:
    ...


def _collaborator_planner(
    planner: RuntimeCollaboratorPlanner | RuntimePlanRequestPlanner | None,
) -> RuntimeCollaboratorPlanner:
    if planner is None:
        return RuntimeCollaboratorPlanner.create_default()
    if isinstance(planner, RuntimePlanRequestPlanner):
        return planner.collaborators
    return planner


def build_runtime_contract_selection(
    *,
    usecases: NavigatorUseCases | None = None,
    contracts: NavigatorRuntimeContracts | None = None,
    planner: RuntimeContractPlanner | RuntimePlanRequestPlanner | None = None,
) -> RuntimeContractSelection:
    """Create the contract selection descriptor for a runtime plan."""

    return _contract_planner(planner).select(
        usecases=usecases, contracts=contracts
    )


def build_runtime_collaborators(
    *,
    scope: Scope,
    dependencies: RuntimePlannerDependencies | None = None,
    planner: RuntimeCollaboratorPlanner | RuntimePlanRequestPlanner | None = None,
) -> RuntimeCollaboratorRequest:
    """Create the collaborator request for a runtime plan."""

    return _collaborator_planner(planner).request(
        scope=scope,
        dependencies=dependencies,
    )


def create_runtime_plan_request(
    *,
    scope: Scope,
    usecases: NavigatorUseCases | None = None,
    contracts: NavigatorRuntimeContracts | None = None,
    dependencies: RuntimePlannerDependencies | None = None,
    planner: RuntimePlanRequestPlanner | None = None,
) -> RuntimePlanRequest:
    """Build a runtime plan request aggregating domain and infrastructure inputs."""

    resolved_planner = planner or RuntimePlanRequestPlanner.create_default()
    return resolved_planner.build(
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
    "RuntimeCollaboratorPlanner",
    "RuntimeContractPlanner",
    "RuntimePlanRequestPlanner",
    "RuntimeAssemblyPlan",
    "RuntimePlannerDependencies",
    "build_navigator_runtime",
    "build_runtime_collaborators",
    "build_runtime_contract_selection",
    "create_runtime_plan",
    "create_runtime_plan_request",
]

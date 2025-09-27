"""Planning helpers for constructing runtime assembly requests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from navigator.core.value.message import Scope

from .contracts import NavigatorRuntimeContracts, RuntimeContractSelection
from .runtime_inputs import RuntimeCollaboratorRequest
from .runtime_plan import RuntimePlanRequest
from .bundler import PayloadBundler
from .runtime_collaborator_factory import RuntimeCollaboratorFactory
from .runtime_contract_selector import RuntimeContractSelector
from .runtime_plan_dependencies import (
    RuntimeInstrumentationDependencies,
    RuntimeNotificationDependencies,
)
from .runtime_plan_request_builder import RuntimePlanRequestBuilder
from .usecases import NavigatorUseCases


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


class ContractPlanning(Protocol):
    """Expose a narrow contract selection capability."""

    def select(
        self,
        *,
        usecases: NavigatorUseCases | None = None,
        contracts: NavigatorRuntimeContracts | None = None,
    ) -> RuntimeContractSelection:
        ...


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


def build_runtime_contract_selection(
    *,
    usecases: NavigatorUseCases | None = None,
    contracts: NavigatorRuntimeContracts | None = None,
    planner: ContractPlanning | None = None,
) -> RuntimeContractSelection:
    """Create the contract selection descriptor for a runtime plan."""

    candidate = planner or RuntimeContractPlanner.create_default()
    return candidate.select(usecases=usecases, contracts=contracts)


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
    "RuntimeCollaboratorPlanner",
    "RuntimeContractPlanner",
    "RuntimePlanRequestPlanner",
    "build_runtime_collaborators",
    "build_runtime_contract_selection",
    "create_runtime_plan_request",
]

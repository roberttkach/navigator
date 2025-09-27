"""Factory helpers building the navigator runtime."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.locks.guard import Guardian
from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .contracts import NavigatorRuntimeContracts, RuntimeContractSelection
from .reporter import NavigatorReporter
from .runtime import NavigatorRuntime
from .runtime_assembler import NavigatorRuntimeAssembler
from .runtime_inputs import RuntimeCollaboratorRequest
from .runtime_plan import RuntimeAssemblyPlan, RuntimePlanRequest, create_runtime_plan
from .runtime_plan_request_builder import (
    RuntimeCollaboratorFactory,
    RuntimeContractSelector,
    RuntimePlanRequestBuilder,
)
from .tail_components import TailTelemetry
from .types import MissingAlert
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
        telemetry: Telemetry | None = None,
        bundler: PayloadBundler | None = None,
        reporter: NavigatorReporter | None = None,
        missing_alert: MissingAlert | None = None,
        tail_telemetry: TailTelemetry | None = None,
    ) -> RuntimeCollaboratorRequest:
        return self.collaborators.create(
            scope=scope,
            telemetry=telemetry,
            reporter=reporter,
            bundler=bundler,
            tail_telemetry=tail_telemetry,
            missing_alert=missing_alert,
        )

    def plan_request(
        self,
        *,
        scope: Scope,
        usecases: NavigatorUseCases | None = None,
        contracts: NavigatorRuntimeContracts | None = None,
        telemetry: Telemetry | None = None,
        bundler: PayloadBundler | None = None,
        reporter: NavigatorReporter | None = None,
        missing_alert: MissingAlert | None = None,
        tail_telemetry: TailTelemetry | None = None,
    ) -> RuntimePlanRequest:
        return self.builder.build(
            scope=scope,
            usecases=usecases,
            contracts=contracts,
            telemetry=telemetry,
            bundler=bundler,
            reporter=reporter,
            missing_alert=missing_alert,
            tail_telemetry=tail_telemetry,
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
    telemetry: Telemetry | None = None,
    bundler: PayloadBundler | None = None,
    reporter: NavigatorReporter | None = None,
    missing_alert: MissingAlert | None = None,
    tail_telemetry: TailTelemetry | None = None,
    planner: NavigatorRuntimePlanner | None = None,
) -> RuntimeCollaboratorRequest:
    """Create the collaborator request for a runtime plan."""

    return _planner(planner).collaborators_request(
        scope=scope,
        telemetry=telemetry,
        reporter=reporter,
        bundler=bundler,
        tail_telemetry=tail_telemetry,
        missing_alert=missing_alert,
    )


def create_runtime_plan_request(
    *,
    scope: Scope,
    usecases: NavigatorUseCases | None = None,
    contracts: NavigatorRuntimeContracts | None = None,
    telemetry: Telemetry | None = None,
    bundler: PayloadBundler | None = None,
    reporter: NavigatorReporter | None = None,
    missing_alert: MissingAlert | None = None,
    tail_telemetry: TailTelemetry | None = None,
    planner: NavigatorRuntimePlanner | None = None,
) -> RuntimePlanRequest:
    """Build a runtime plan request aggregating domain and infrastructure inputs."""

    return _planner(planner).plan_request(
        scope=scope,
        usecases=usecases,
        contracts=contracts,
        telemetry=telemetry,
        bundler=bundler,
        reporter=reporter,
        missing_alert=missing_alert,
        tail_telemetry=tail_telemetry,
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
    "build_navigator_runtime",
    "build_runtime_collaborators",
    "build_runtime_contract_selection",
    "create_runtime_plan",
    "create_runtime_plan_request",
]

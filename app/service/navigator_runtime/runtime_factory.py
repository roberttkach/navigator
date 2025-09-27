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


_CONTRACT_SELECTOR = RuntimeContractSelector()
_COLLABORATOR_FACTORY = RuntimeCollaboratorFactory()
_PLAN_REQUEST_BUILDER = RuntimePlanRequestBuilder(
    contract_selector=_CONTRACT_SELECTOR,
    collaborator_factory=_COLLABORATOR_FACTORY,
)


def build_runtime_contract_selection(
    *,
    usecases: NavigatorUseCases | None = None,
    contracts: NavigatorRuntimeContracts | None = None,
) -> RuntimeContractSelection:
    """Create the contract selection descriptor for a runtime plan."""

    return _CONTRACT_SELECTOR.select(usecases=usecases, contracts=contracts)


def build_runtime_collaborators(
    *,
    scope: Scope,
    telemetry: Telemetry | None = None,
    bundler: PayloadBundler | None = None,
    reporter: NavigatorReporter | None = None,
    missing_alert: MissingAlert | None = None,
    tail_telemetry: TailTelemetry | None = None,
) -> RuntimeCollaboratorRequest:
    """Create the collaborator request for a runtime plan."""

    return _COLLABORATOR_FACTORY.create(
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
) -> RuntimePlanRequest:
    """Build a runtime plan request aggregating domain and infrastructure inputs."""

    return _PLAN_REQUEST_BUILDER.build(
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
    "RuntimeAssemblyPlan",
    "build_navigator_runtime",
    "build_runtime_collaborators",
    "build_runtime_contract_selection",
    "create_runtime_plan",
    "create_runtime_plan_request",
]

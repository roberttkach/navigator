"""Builders producing runtime plan requests from domain inputs."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .contracts import NavigatorRuntimeContracts, RuntimeContractSelection
from .reporter import NavigatorReporter
from .runtime_inputs import RuntimeCollaboratorRequest
from .runtime_plan import RuntimePlanRequest
from .tail_components import TailTelemetry
from .types import MissingAlert
from .usecases import NavigatorUseCases


@dataclass(frozen=True)
class RuntimePlannerDependencies:
    """Bundle optional collaborators used during plan creation."""

    telemetry: Telemetry | None = None
    bundler: PayloadBundler | None = None
    reporter: NavigatorReporter | None = None
    missing_alert: MissingAlert | None = None
    tail_telemetry: TailTelemetry | None = None


@dataclass(frozen=True)
class RuntimeContractSelector:
    """Build contract selections isolating domain knowledge."""

    def select(
        self,
        *,
        usecases: NavigatorUseCases | None = None,
        contracts: NavigatorRuntimeContracts | None = None,
    ) -> RuntimeContractSelection:
        """Return a contract selection wrapper for runtime planning."""

        return RuntimeContractSelection(usecases=usecases, contracts=contracts)


@dataclass(frozen=True)
class RuntimeCollaboratorFactory:
    """Create collaborator requests decoupled from request orchestration."""

    def create(
        self,
        *,
        scope: Scope,
        dependencies: RuntimePlannerDependencies,
    ) -> RuntimeCollaboratorRequest:
        """Return a collaborator request describing runtime auxiliaries."""

        return RuntimeCollaboratorRequest(
            scope=scope,
            telemetry=dependencies.telemetry,
            reporter=dependencies.reporter,
            bundler=dependencies.bundler,
            tail_telemetry=dependencies.tail_telemetry,
            missing_alert=dependencies.missing_alert,
        )


@dataclass(frozen=True)
class RuntimePlanRequestBuilder:
    """Coordinate individual builders to produce runtime plan requests."""

    contract_selector: RuntimeContractSelector
    collaborator_factory: RuntimeCollaboratorFactory

    def build(
        self,
        *,
        scope: Scope,
        usecases: NavigatorUseCases | None = None,
        contracts: NavigatorRuntimeContracts | None = None,
        dependencies: RuntimePlannerDependencies,
    ) -> RuntimePlanRequest:
        """Create a runtime plan request aggregating domain and tooling inputs."""

        contract_source = self.contract_selector.select(
            usecases=usecases,
            contracts=contracts,
        )
        collaborator_request = self.collaborator_factory.create(
            scope=scope,
            dependencies=dependencies,
        )
        return RuntimePlanRequest(
            contracts=contract_source,
            collaborators=collaborator_request,
        )


__all__ = [
    "RuntimeCollaboratorFactory",
    "RuntimeContractSelector",
    "RuntimePlanRequestBuilder",
    "RuntimePlannerDependencies",
]

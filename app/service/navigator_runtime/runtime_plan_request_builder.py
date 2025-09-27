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
class RuntimeInstrumentationDependencies:
    """Capture telemetry-related collaborators for runtime planning."""

    telemetry: Telemetry | None = None
    tail: TailTelemetry | None = None


@dataclass(frozen=True)
class RuntimeNotificationDependencies:
    """Capture notification components required during runtime planning."""

    reporter: NavigatorReporter | None = None
    missing_alert: MissingAlert | None = None


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
        instrumentation: RuntimeInstrumentationDependencies | None = None,
        notifications: RuntimeNotificationDependencies | None = None,
        bundler: PayloadBundler | None = None,
    ) -> RuntimeCollaboratorRequest:
        """Return a collaborator request describing runtime auxiliaries."""

        instrumentation = instrumentation or RuntimeInstrumentationDependencies()
        notifications = notifications or RuntimeNotificationDependencies()
        return RuntimeCollaboratorRequest(
            scope=scope,
            telemetry=instrumentation.telemetry,
            reporter=notifications.reporter,
            bundler=bundler,
            tail_telemetry=instrumentation.tail,
            missing_alert=notifications.missing_alert,
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
        instrumentation: RuntimeInstrumentationDependencies | None = None,
        notifications: RuntimeNotificationDependencies | None = None,
        bundler: PayloadBundler | None = None,
    ) -> RuntimePlanRequest:
        """Create a runtime plan request aggregating domain and tooling inputs."""

        contract_source = self.contract_selector.select(
            usecases=usecases,
            contracts=contracts,
        )
        collaborator_request = self.collaborator_factory.create(
            scope=scope,
            instrumentation=instrumentation,
            notifications=notifications,
            bundler=bundler,
        )
        return RuntimePlanRequest(
            contracts=contract_source,
            collaborators=collaborator_request,
        )


__all__ = [
    "RuntimeCollaboratorFactory",
    "RuntimeContractSelector",
    "RuntimePlanRequestBuilder",
    "RuntimeInstrumentationDependencies",
    "RuntimeNotificationDependencies",
]

"""Builders producing runtime plan requests from domain inputs."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .contracts import NavigatorRuntimeContracts
from .runtime_collaborator_factory import RuntimeCollaboratorFactory
from .runtime_contract_selector import RuntimeContractSelector
from .runtime_inputs import RuntimeCollaboratorRequest
from .runtime_plan import RuntimePlanRequest
from .runtime_plan_dependencies import (
    RuntimeInstrumentationDependencies,
    RuntimeNotificationDependencies,
)
from .usecases import NavigatorUseCases


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
    "RuntimePlanRequestBuilder",
]

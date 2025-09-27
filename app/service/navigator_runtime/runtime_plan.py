"""Planning helpers describing runtime assembly inputs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .contracts import NavigatorRuntimeContracts
from .reporter import NavigatorReporter
from .runtime_inputs import (
    RuntimeCollaborators,
    prepare_runtime_collaborators,
    resolve_runtime_contracts,
)
from .tail_components import TailTelemetry
from .types import MissingAlert
from .usecases import NavigatorUseCases


@dataclass(frozen=True)
class ComponentAssemblyRequest:
    """Describe how a specific runtime component should be built."""

    contract: object
    parameters: Mapping[str, Any]

    def build_with(self, builder: object) -> object:
        """Execute the build action against the provided component builder."""

        return builder.build(self.contract, **self.parameters)


@dataclass(frozen=True)
class RuntimeAssemblyPlan:
    """Describe the collaborators required to assemble the runtime."""

    history: ComponentAssemblyRequest
    state: ComponentAssemblyRequest
    tail: ComponentAssemblyRequest


def create_runtime_plan(
    *,
    usecases: NavigatorUseCases | None,
    contracts: NavigatorRuntimeContracts | None,
    scope: Scope,
    telemetry: Telemetry | None,
    bundler: PayloadBundler | None,
    reporter: NavigatorReporter | None,
    missing_alert: MissingAlert | None,
    tail_telemetry: TailTelemetry | None,
) -> RuntimeAssemblyPlan:
    """Resolve runtime collaborators and contracts into a buildable plan."""

    resolved_contracts = resolve_runtime_contracts(
        usecases=usecases, contracts=contracts
    )
    collaborators = prepare_runtime_collaborators(
        scope=scope,
        telemetry=telemetry,
        reporter=reporter,
        bundler=bundler,
        tail_telemetry=tail_telemetry,
        missing_alert=missing_alert,
    )
    history = ComponentAssemblyRequest(
        contract=resolved_contracts.history,
        parameters={
            "reporter": collaborators.reporter,
            "bundler": collaborators.bundler,
        },
    )
    state = ComponentAssemblyRequest(
        contract=resolved_contracts.state,
        parameters={
            "reporter": collaborators.reporter,
            "missing_alert": collaborators.missing_alert,
        },
    )
    tail = ComponentAssemblyRequest(
        contract=resolved_contracts.tail,
        parameters={
            "telemetry": collaborators.telemetry,
            "tail_telemetry": collaborators.tail_telemetry,
        },
    )
    return RuntimeAssemblyPlan(history=history, state=state, tail=tail)


__all__ = [
    "ComponentAssemblyRequest",
    "RuntimeAssemblyPlan",
    "create_runtime_plan",
]

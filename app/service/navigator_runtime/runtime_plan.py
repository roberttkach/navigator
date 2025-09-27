"""Planning helpers describing runtime assembly inputs."""
from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Protocol

from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .contracts import HistoryContracts, NavigatorRuntimeContracts, StateContracts, TailContracts
from .reporter import NavigatorReporter
from .runtime_inputs import (
    RuntimeCollaborators,
    prepare_runtime_collaborators,
    resolve_runtime_contracts,
)
from .tail_components import TailTelemetry
from .types import MissingAlert
from .usecases import NavigatorUseCases

if TYPE_CHECKING:
    from .history import NavigatorHistoryService
    from .state import NavigatorStateService
    from .tail import NavigatorTail


class HistoryComponentBuilder(Protocol):
    """Protocol describing builders for history services."""

    def build_component(self, request: "HistoryAssemblyRequest") -> "NavigatorHistoryService": ...


class StateComponentBuilder(Protocol):
    """Protocol describing builders for state services."""

    def build_component(self, request: "StateAssemblyRequest") -> "NavigatorStateService": ...


class TailComponentBuilder(Protocol):
    """Protocol describing builders for tail services."""

    def build_component(self, request: "TailAssemblyRequest") -> "NavigatorTail": ...


@dataclass(frozen=True)
class HistoryAssemblyRequest:
    """Capture inputs required to assemble history services."""

    contract: HistoryContracts
    reporter: NavigatorReporter
    bundler: PayloadBundler

    def build_with(self, builder: HistoryComponentBuilder) -> "NavigatorHistoryService":
        """Delegate construction to the provided history builder."""

        return builder.build_component(self)


@dataclass(frozen=True)
class StateAssemblyRequest:
    """Capture inputs required to assemble state services."""

    contract: StateContracts
    reporter: NavigatorReporter
    missing_alert: MissingAlert | None

    def build_with(self, builder: StateComponentBuilder) -> "NavigatorStateService":
        """Delegate construction to the provided state builder."""

        return builder.build_component(self)


@dataclass(frozen=True)
class TailAssemblyRequest:
    """Capture inputs required to assemble tail services."""

    contract: TailContracts
    telemetry: Telemetry | None
    tail_telemetry: TailTelemetry | None

    def build_with(self, builder: TailComponentBuilder) -> "NavigatorTail":
        """Delegate construction to the provided tail builder."""

        return builder.build_component(self)


@dataclass(frozen=True)
class RuntimeAssemblyPlan:
    """Describe the collaborators required to assemble the runtime."""

    history: HistoryAssemblyRequest
    state: StateAssemblyRequest
    tail: TailAssemblyRequest


@dataclass(frozen=True)
class RuntimePlanInputs:
    """Pair resolved contracts with supporting runtime collaborators."""

    contracts: NavigatorRuntimeContracts
    collaborators: RuntimeCollaborators


def resolve_runtime_plan_inputs(
    *,
    usecases: NavigatorUseCases | None,
    contracts: NavigatorRuntimeContracts | None,
    scope: Scope,
    telemetry: Telemetry | None,
    bundler: PayloadBundler | None,
    reporter: NavigatorReporter | None,
    missing_alert: MissingAlert | None,
    tail_telemetry: TailTelemetry | None,
) -> RuntimePlanInputs:
    """Resolve runtime contracts and collaborators in two independent steps."""

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
    return RuntimePlanInputs(contracts=resolved_contracts, collaborators=collaborators)


def build_runtime_plan(inputs: RuntimePlanInputs) -> RuntimeAssemblyPlan:
    """Create a runtime assembly plan from resolved inputs."""

    history = HistoryAssemblyRequest(
        contract=inputs.contracts.history,
        reporter=inputs.collaborators.reporter,
        bundler=inputs.collaborators.bundler,
    )
    state = StateAssemblyRequest(
        contract=inputs.contracts.state,
        reporter=inputs.collaborators.reporter,
        missing_alert=inputs.collaborators.missing_alert,
    )
    tail = TailAssemblyRequest(
        contract=inputs.contracts.tail,
        telemetry=inputs.collaborators.telemetry,
        tail_telemetry=inputs.collaborators.tail_telemetry,
    )
    return RuntimeAssemblyPlan(history=history, state=state, tail=tail)


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

    inputs = resolve_runtime_plan_inputs(
        usecases=usecases,
        contracts=contracts,
        scope=scope,
        telemetry=telemetry,
        bundler=bundler,
        reporter=reporter,
        missing_alert=missing_alert,
        tail_telemetry=tail_telemetry,
    )
    return build_runtime_plan(inputs)


__all__ = [
    "HistoryAssemblyRequest",
    "RuntimeAssemblyPlan",
    "RuntimePlanInputs",
    "StateAssemblyRequest",
    "TailAssemblyRequest",
    "build_runtime_plan",
    "create_runtime_plan",
    "resolve_runtime_plan_inputs",
]

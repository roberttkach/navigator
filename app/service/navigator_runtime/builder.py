"""Factory helpers building the navigator runtime."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.locks.guard import Guardian
from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .contracts import (
    HistoryContracts,
    NavigatorRuntimeContracts,
    StateContracts,
    TailContracts,
)
from .history import NavigatorHistoryService
from .history_builder import build_history_service
from .reporter import NavigatorReporter
from .runtime import NavigatorRuntime
from .state import NavigatorStateService
from .state_builder import build_state_service
from .tail import NavigatorTail
from .tail_builder import build_tail_service
from .tail_components import TailTelemetry
from .types import MissingAlert
from .usecases import NavigatorUseCases
from .runtime_inputs import (
    RuntimeCollaborators,
    prepare_runtime_collaborators,
    resolve_runtime_contracts,
)


@dataclass(frozen=True)
class RuntimeBuildContext:
    """Shared context values used across specialised runtime builders."""

    guard: Guardian
    scope: Scope


@dataclass(frozen=True)
class HistoryServiceBuilder:
    """Construct history services using consistent runtime context."""

    context: RuntimeBuildContext

    def build(
        self,
        contracts: HistoryContracts,
        *,
        reporter: NavigatorReporter,
        bundler: PayloadBundler,
    ) -> NavigatorHistoryService:
        return build_history_service(
            contracts,
            guard=self.context.guard,
            scope=self.context.scope,
            reporter=reporter,
            bundler=bundler,
        )


@dataclass(frozen=True)
class StateServiceBuilder:
    """Create state services while isolating dependency wiring."""

    context: RuntimeBuildContext

    def build(
        self,
        contracts: StateContracts,
        *,
        reporter: NavigatorReporter,
        missing_alert: MissingAlert | None,
    ) -> NavigatorStateService:
        return build_state_service(
            contracts,
            guard=self.context.guard,
            scope=self.context.scope,
            reporter=reporter,
            missing_alert=missing_alert,
        )


@dataclass(frozen=True)
class TailServiceBuilder:
    """Prepare tail services with explicit runtime context."""

    context: RuntimeBuildContext

    def build(
        self,
        contracts: TailContracts,
        *,
        telemetry: Telemetry | None,
        tail_telemetry: TailTelemetry | None,
    ) -> NavigatorTail:
        return build_tail_service(
            contracts,
            guard=self.context.guard,
            scope=self.context.scope,
            telemetry=telemetry,
            tail_telemetry=tail_telemetry,
        )


@dataclass(frozen=True)
class RuntimeAssemblyPlan:
    """Describe the collaborators required to assemble the runtime."""

    contracts: NavigatorRuntimeContracts
    collaborators: RuntimeCollaborators


@dataclass(frozen=True)
class RuntimeComponentBuilders:
    """Group component-specific builders under a shared context."""

    history: HistoryServiceBuilder
    state: StateServiceBuilder
    tail: TailServiceBuilder

    @classmethod
    def for_context(cls, context: RuntimeBuildContext) -> "RuntimeComponentBuilders":
        return cls(
            history=HistoryServiceBuilder(context),
            state=StateServiceBuilder(context),
            tail=TailServiceBuilder(context),
        )


class NavigatorRuntimeBuilder:
    """Incrementally assemble navigator runtime components."""

    def __init__(self, builders: RuntimeComponentBuilders) -> None:
        self._builders = builders

    @classmethod
    def from_context(
        cls, *, guard: Guardian, scope: Scope
    ) -> "NavigatorRuntimeBuilder":
        context = RuntimeBuildContext(guard=guard, scope=scope)
        return cls(RuntimeComponentBuilders.for_context(context))

    def build_history(
        self,
        contracts: HistoryContracts,
        *,
        reporter: NavigatorReporter,
        bundler: PayloadBundler,
    ) -> NavigatorHistoryService:
        return self._builders.history.build(
            contracts,
            reporter=reporter,
            bundler=bundler,
        )

    def build_state(
        self,
        contracts: StateContracts,
        *,
        reporter: NavigatorReporter,
        missing_alert: MissingAlert | None,
    ) -> NavigatorStateService:
        return self._builders.state.build(
            contracts,
            reporter=reporter,
            missing_alert=missing_alert,
        )

    def build_tail(
        self,
        contracts: TailContracts,
        *,
        telemetry: Telemetry | None,
        tail_telemetry: TailTelemetry | None,
    ) -> NavigatorTail:
        return self._builders.tail.build(
            contracts,
            telemetry=telemetry,
            tail_telemetry=tail_telemetry,
        )

    def assemble(
        self,
        *,
        contracts: NavigatorRuntimeContracts,
        collaborators: RuntimeCollaborators,
    ) -> NavigatorRuntime:
        history = self.build_history(
            contracts.history,
            reporter=collaborators.reporter,
            bundler=collaborators.bundler,
        )
        state = self.build_state(
            contracts.state,
            reporter=collaborators.reporter,
            missing_alert=collaborators.missing_alert,
        )
        tail = self.build_tail(
            contracts.tail,
            telemetry=collaborators.telemetry,
            tail_telemetry=collaborators.tail_telemetry,
        )
        return NavigatorRuntime(history=history, state=state, tail=tail)


class NavigatorRuntimeAssembler:
    """Coordinate builder usage around a well-defined assembly plan."""

    def __init__(self, builder: NavigatorRuntimeBuilder) -> None:
        self._builder = builder

    @classmethod
    def from_context(
        cls, *, guard: Guardian, scope: Scope
    ) -> "NavigatorRuntimeAssembler":
        return cls(NavigatorRuntimeBuilder.from_context(guard=guard, scope=scope))

    def assemble(self, plan: RuntimeAssemblyPlan) -> NavigatorRuntime:
        return self._builder.assemble(
            contracts=plan.contracts,
            collaborators=plan.collaborators,
        )


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
    return RuntimeAssemblyPlan(
        contracts=resolved_contracts,
        collaborators=collaborators,
    )


def build_navigator_runtime(
    *,
    usecases: NavigatorUseCases | None = None,
    contracts: NavigatorRuntimeContracts | None = None,
    scope: Scope,
    guard: Guardian,
    telemetry: Telemetry | None = None,
    bundler: PayloadBundler | None = None,
    reporter: NavigatorReporter | None = None,
    missing_alert: MissingAlert | None = None,
    tail_telemetry: TailTelemetry | None = None,
) -> NavigatorRuntime:
    """Create a navigator runtime wiring use cases with cross-cutting tools."""

    plan = create_runtime_plan(
        usecases=usecases,
        contracts=contracts,
        scope=scope,
        telemetry=telemetry,
        bundler=bundler,
        reporter=reporter,
        missing_alert=missing_alert,
        tail_telemetry=tail_telemetry,
    )
    assembler = NavigatorRuntimeAssembler.from_context(guard=guard, scope=scope)
    return assembler.assemble(plan)


__all__ = [
    "HistoryServiceBuilder",
    "HistoryContracts",
    "NavigatorRuntimeContracts",
    "RuntimeBuildContext",
    "RuntimeComponentBuilders",
    "RuntimeAssemblyPlan",
    "StateContracts",
    "StateServiceBuilder",
    "TailContracts",
    "TailServiceBuilder",
    "NavigatorRuntimeAssembler",
    "NavigatorRuntimeBuilder",
    "build_navigator_runtime",
    "create_runtime_plan",
]

"""Builders creating runtime service components."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.telemetry import Telemetry

from .bundler import PayloadBundler
from .contracts import HistoryContracts, StateContracts, TailContracts
from .history import NavigatorHistoryService
from .history_builder import build_history_service
from .reporter import NavigatorReporter
from .runtime_context import RuntimeBuildContext
from .state import NavigatorStateService
from .state_builder import build_state_service
from .tail import NavigatorTail
from .tail_builder import build_tail_service
from .tail_components import TailTelemetry
from .types import MissingAlert


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


__all__ = [
    "HistoryServiceBuilder",
    "RuntimeComponentBuilders",
    "StateServiceBuilder",
    "TailServiceBuilder",
]

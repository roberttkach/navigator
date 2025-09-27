"""Factory helpers building the navigator runtime."""
from __future__ import annotations

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


class NavigatorRuntimeBuilder:
    """Incrementally assemble navigator runtime components."""

    def __init__(self, *, guard: Guardian, scope: Scope) -> None:
        self._guard = guard
        self._scope = scope

    def resolve_contracts(
        self,
        *,
        usecases: NavigatorUseCases | None,
        contracts: NavigatorRuntimeContracts | None,
    ) -> NavigatorRuntimeContracts:
        if contracts is not None:
            return contracts
        if usecases is None:
            raise ValueError("either usecases or contracts must be provided")
        return NavigatorRuntimeContracts.from_usecases(usecases)

    @staticmethod
    def resolve_bundler(bundler: PayloadBundler | None) -> PayloadBundler:
        return bundler or PayloadBundler()

    def resolve_reporter(
        self,
        telemetry: Telemetry | None,
        reporter: NavigatorReporter | None,
    ) -> NavigatorReporter:
        if reporter is not None:
            return reporter
        if telemetry is None:
            raise ValueError("telemetry must be provided when reporter is not supplied")
        return NavigatorReporter(telemetry, self._scope)

    @staticmethod
    def ensure_telemetry(telemetry: Telemetry | None, tail_telemetry: TailTelemetry | None) -> None:
        if telemetry is None and tail_telemetry is None:
            raise ValueError("either telemetry or tail_telemetry must be provided")

    def build_history(
        self,
        contracts: HistoryContracts,
        *,
        reporter: NavigatorReporter,
        bundler: PayloadBundler,
    ) -> NavigatorHistoryService:
        return build_history_service(
            contracts,
            guard=self._guard,
            scope=self._scope,
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
        return build_state_service(
            contracts,
            guard=self._guard,
            scope=self._scope,
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
        return build_tail_service(
            contracts,
            guard=self._guard,
            scope=self._scope,
            telemetry=telemetry,
            tail_telemetry=tail_telemetry,
        )

    def assemble(
        self,
        *,
        contracts: NavigatorRuntimeContracts,
        reporter: NavigatorReporter,
        bundler: PayloadBundler,
        telemetry: Telemetry | None,
        tail_telemetry: TailTelemetry | None,
        missing_alert: MissingAlert | None,
    ) -> NavigatorRuntime:
        self.ensure_telemetry(telemetry, tail_telemetry)
        history = self.build_history(contracts.history, reporter=reporter, bundler=bundler)
        state = self.build_state(
            contracts.state,
            reporter=reporter,
            missing_alert=missing_alert,
        )
        tail = self.build_tail(
            contracts.tail,
            telemetry=telemetry,
            tail_telemetry=tail_telemetry,
        )
        return NavigatorRuntime(history=history, state=state, tail=tail)


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

    builder = NavigatorRuntimeBuilder(guard=guard, scope=scope)
    resolved_contracts = builder.resolve_contracts(usecases=usecases, contracts=contracts)
    resolved_bundler = builder.resolve_bundler(bundler)
    resolved_reporter = builder.resolve_reporter(telemetry, reporter)
    return builder.assemble(
        contracts=resolved_contracts,
        reporter=resolved_reporter,
        bundler=resolved_bundler,
        telemetry=telemetry,
        tail_telemetry=tail_telemetry,
        missing_alert=missing_alert,
    )


__all__ = [
    "HistoryContracts",
    "NavigatorRuntimeContracts",
    "StateContracts",
    "TailContracts",
    "NavigatorRuntimeBuilder",
    "build_navigator_runtime",
]

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
from .history_builder import build_history_service
from .reporter import NavigatorReporter
from .runtime import NavigatorRuntime
from .state_builder import build_state_service
from .tail_builder import build_tail_service
from .types import MissingAlert
from .usecases import NavigatorUseCases


def build_navigator_runtime(
    *,
    usecases: NavigatorUseCases | None = None,
    contracts: NavigatorRuntimeContracts | None = None,
    scope: Scope,
    guard: Guardian,
    telemetry: Telemetry,
    bundler: PayloadBundler | None = None,
    reporter: NavigatorReporter | None = None,
    missing_alert: MissingAlert | None = None,
) -> NavigatorRuntime:
    """Create a navigator runtime wiring use cases with cross-cutting tools."""

    if contracts is None:
        if usecases is None:
            raise ValueError("either usecases or contracts must be provided")
        contracts = NavigatorRuntimeContracts.from_usecases(usecases)

    bundler = bundler or PayloadBundler()
    reporter = reporter or NavigatorReporter(telemetry, scope)

    history = build_history_service(
        contracts.history,
        guard=guard,
        scope=scope,
        reporter=reporter,
        bundler=bundler,
    )
    state = build_state_service(
        contracts.state,
        guard=guard,
        scope=scope,
        reporter=reporter,
        missing_alert=missing_alert,
    )
    tail = build_tail_service(
        contracts.tail,
        guard=guard,
        scope=scope,
        telemetry=telemetry,
    )
    return NavigatorRuntime(history=history, state=state, tail=tail)


__all__ = [
    "HistoryContracts",
    "NavigatorRuntimeContracts",
    "StateContracts",
    "TailContracts",
    "build_navigator_runtime",
]

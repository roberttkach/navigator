"""Factory helpers building the navigator runtime."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.locks.guard import Guardian
from navigator.app.usecase.alarm import Alarm
from navigator.app.usecase.last import Tailer
from navigator.app.usecase.set import Setter
from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .history import (
    HistoryAddOperation,
    HistoryBackOperation,
    HistoryRebaseOperation,
    HistoryReplaceOperation,
    HistoryTrimOperation,
    NavigatorHistoryService,
)
from .reporter import NavigatorReporter
from .runtime import NavigatorRuntime
from .state import MissingStateAlarm, NavigatorStateService
from .tail import NavigatorTail
from .tail_components import TailGateway, TailLocker, TailTelemetry
from .types import MissingAlert
from .usecases import NavigatorUseCases
from .ports import (
    AppendHistoryUseCase,
    ReplaceHistoryUseCase,
    RebaseHistoryUseCase,
    RewindHistoryUseCase,
    TrimHistoryUseCase,
)


@dataclass(frozen=True)
class HistoryContracts:
    """Expose the history-specific collaborators required by the runtime."""

    appender: AppendHistoryUseCase
    swapper: ReplaceHistoryUseCase
    shifter: RebaseHistoryUseCase
    rewinder: RewindHistoryUseCase
    trimmer: TrimHistoryUseCase


@dataclass(frozen=True)
class StateContracts:
    """Expose state-oriented use cases required by the runtime."""

    setter: Setter
    alarm: Alarm


@dataclass(frozen=True)
class TailContracts:
    """Expose tail-specific collaborators required by the runtime."""

    tailer: Tailer


@dataclass(frozen=True)
class NavigatorRuntimeContracts:
    """Group per-service contracts consumed by the runtime builder."""

    history: HistoryContracts
    state: StateContracts
    tail: TailContracts

    @classmethod
    def from_usecases(cls, usecases: NavigatorUseCases) -> "NavigatorRuntimeContracts":
        return cls(
            history=HistoryContracts(
                appender=usecases.appender,
                swapper=usecases.swapper,
                shifter=usecases.shifter,
                rewinder=usecases.rewinder,
                trimmer=usecases.trimmer,
            ),
            state=StateContracts(
                setter=usecases.setter,
                alarm=usecases.alarm,
            ),
            tail=TailContracts(
                tailer=usecases.tailer,
            ),
        )


@dataclass(frozen=True)
class _HistoryAssemblyContext:
    """Share cross-cutting concerns required for history operations."""

    guard: Guardian
    scope: Scope
    reporter: NavigatorReporter
    bundler: PayloadBundler


class _HistoryServiceAssembler:
    """Create history operations using dedicated assembly context."""

    def __init__(self, contracts: HistoryContracts, context: _HistoryAssemblyContext) -> None:
        self._contracts = contracts
        self._context = context

    def create(self) -> NavigatorHistoryService:
        return NavigatorHistoryService(
            add=self._build_add(),
            replace=self._build_replace(),
            rebase=self._build_rebase(),
            back=self._build_back(),
            pop=self._build_trim(),
        )

    def _build_add(self) -> HistoryAddOperation:
        return HistoryAddOperation(
            appender=self._contracts.appender,
            bundler=self._context.bundler,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )

    def _build_replace(self) -> HistoryReplaceOperation:
        return HistoryReplaceOperation(
            swapper=self._contracts.swapper,
            bundler=self._context.bundler,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )

    def _build_rebase(self) -> HistoryRebaseOperation:
        return HistoryRebaseOperation(
            shifter=self._contracts.shifter,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )

    def _build_back(self) -> HistoryBackOperation:
        return HistoryBackOperation(
            rewinder=self._contracts.rewinder,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )

    def _build_trim(self) -> HistoryTrimOperation:
        return HistoryTrimOperation(
            trimmer=self._contracts.trimmer,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )


@dataclass(frozen=True)
class _StateAssemblyContext:
    """Collect collaborators shared by state services."""

    guard: Guardian
    scope: Scope
    reporter: NavigatorReporter
    missing_alert: MissingAlert | None


class _StateServiceAssembler:
    """Create navigator state services with explicit dependencies."""

    def __init__(self, contracts: StateContracts, context: _StateAssemblyContext) -> None:
        self._contracts = contracts
        self._context = context

    def create(self) -> NavigatorStateService:
        alarm = MissingStateAlarm(
            alarm=self._contracts.alarm,
            scope=self._context.scope,
            factory=self._context.missing_alert,
        )
        return NavigatorStateService(
            setter=self._contracts.setter,
            alarm=self._contracts.alarm,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
            missing_alarm=alarm,
        )


@dataclass(frozen=True)
class _TailAssemblyContext:
    """Provide the shared dependencies required for tail assembly."""

    guard: Guardian
    scope: Scope
    telemetry: Telemetry


class _TailServiceAssembler:
    """Assemble tail services decoupled from other contexts."""

    def __init__(self, contracts: TailContracts, context: _TailAssemblyContext) -> None:
        self._contracts = contracts
        self._context = context

    def create(self) -> NavigatorTail:
        gateway = TailGateway(self._contracts.tailer)
        locker = TailLocker(self._context.guard, self._context.scope)
        telemetry = TailTelemetry.from_telemetry(
            self._context.telemetry,
            self._context.scope,
        )
        return NavigatorTail(gateway=gateway, locker=locker, telemetry=telemetry)


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
    history_context = _HistoryAssemblyContext(
        guard=guard,
        scope=scope,
        reporter=reporter,
        bundler=bundler,
    )
    state_context = _StateAssemblyContext(
        guard=guard,
        scope=scope,
        reporter=reporter,
        missing_alert=missing_alert,
    )
    tail_context = _TailAssemblyContext(
        guard=guard,
        scope=scope,
        telemetry=telemetry,
    )
    history = _HistoryServiceAssembler(contracts.history, history_context).create()
    state = _StateServiceAssembler(contracts.state, state_context).create()
    tail = _TailServiceAssembler(contracts.tail, tail_context).create()
    return NavigatorRuntime(history=history, state=state, tail=tail)


__all__ = [
    "HistoryContracts",
    "NavigatorRuntimeContracts",
    "StateContracts",
    "TailContracts",
    "build_navigator_runtime",
]

"""Factory helpers building the navigator runtime."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.locks.guard import Guardian
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


@dataclass(frozen=True)
class _HistoryAssemblyContext:
    """Share cross-cutting concerns required for history operations."""

    guard: Guardian
    scope: Scope
    reporter: NavigatorReporter
    bundler: PayloadBundler


class _HistoryServiceAssembler:
    """Create history operations using dedicated assembly context."""

    def __init__(self, usecases: NavigatorUseCases, context: _HistoryAssemblyContext) -> None:
        self._usecases = usecases
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
            appender=self._usecases.appender,
            bundler=self._context.bundler,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )

    def _build_replace(self) -> HistoryReplaceOperation:
        return HistoryReplaceOperation(
            swapper=self._usecases.swapper,
            bundler=self._context.bundler,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )

    def _build_rebase(self) -> HistoryRebaseOperation:
        return HistoryRebaseOperation(
            shifter=self._usecases.shifter,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )

    def _build_back(self) -> HistoryBackOperation:
        return HistoryBackOperation(
            rewinder=self._usecases.rewinder,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )

    def _build_trim(self) -> HistoryTrimOperation:
        return HistoryTrimOperation(
            trimmer=self._usecases.trimmer,
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

    def __init__(self, usecases: NavigatorUseCases, context: _StateAssemblyContext) -> None:
        self._usecases = usecases
        self._context = context

    def create(self) -> NavigatorStateService:
        alarm = MissingStateAlarm(
            alarm=self._usecases.alarm,
            scope=self._context.scope,
            factory=self._context.missing_alert,
        )
        return NavigatorStateService(
            setter=self._usecases.setter,
            alarm=self._usecases.alarm,
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

    def __init__(self, usecases: NavigatorUseCases, context: _TailAssemblyContext) -> None:
        self._usecases = usecases
        self._context = context

    def create(self) -> NavigatorTail:
        gateway = TailGateway(self._usecases.tailer)
        locker = TailLocker(self._context.guard, self._context.scope)
        telemetry = TailTelemetry.from_telemetry(
            self._context.telemetry,
            self._context.scope,
        )
        return NavigatorTail(gateway=gateway, locker=locker, telemetry=telemetry)


def build_navigator_runtime(
    *,
    usecases: NavigatorUseCases,
    scope: Scope,
    guard: Guardian,
    telemetry: Telemetry,
    bundler: PayloadBundler | None = None,
    reporter: NavigatorReporter | None = None,
    missing_alert: MissingAlert | None = None,
) -> NavigatorRuntime:
    """Create a navigator runtime wiring use cases with cross-cutting tools."""

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
    history = _HistoryServiceAssembler(usecases, history_context).create()
    state = _StateServiceAssembler(usecases, state_context).create()
    tail = _TailServiceAssembler(usecases, tail_context).create()
    return NavigatorRuntime(history=history, state=state, tail=tail)


__all__ = ["build_navigator_runtime"]

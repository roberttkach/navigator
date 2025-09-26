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
from .types import MissingAlert
from .usecases import NavigatorUseCases


@dataclass
class _RuntimeContext:
    """Aggregate cross-cutting collaborators shared across runtime services."""

    guard: Guardian
    scope: Scope
    telemetry: Telemetry
    reporter: NavigatorReporter
    bundler: PayloadBundler
    missing_alert: MissingAlert | None = None


class _NavigatorRuntimeAssembler:
    """Compose runtime services from use cases and shared collaborators."""

    def __init__(self, *, usecases: NavigatorUseCases, context: _RuntimeContext) -> None:
        self._usecases = usecases
        self._context = context

    def history(self) -> NavigatorHistoryService:
        return NavigatorHistoryService(
            add=self._create_add_operation(),
            replace=self._create_replace_operation(),
            rebase=self._create_rebase_operation(),
            back=self._create_back_operation(),
            pop=self._create_trim_operation(),
        )

    def state(self) -> NavigatorStateService:
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

    def tail(self) -> NavigatorTail:
        return NavigatorTail(
            flow=self._usecases.tailer,
            scope=self._context.scope,
            guard=self._context.guard,
            telemetry=self._context.telemetry,
        )

    def _create_add_operation(self) -> HistoryAddOperation:
        return HistoryAddOperation(
            appender=self._usecases.appender,
            bundler=self._context.bundler,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )

    def _create_replace_operation(self) -> HistoryReplaceOperation:
        return HistoryReplaceOperation(
            swapper=self._usecases.swapper,
            bundler=self._context.bundler,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )

    def _create_rebase_operation(self) -> HistoryRebaseOperation:
        return HistoryRebaseOperation(
            shifter=self._usecases.shifter,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )

    def _create_back_operation(self) -> HistoryBackOperation:
        return HistoryBackOperation(
            rewinder=self._usecases.rewinder,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )

    def _create_trim_operation(self) -> HistoryTrimOperation:
        return HistoryTrimOperation(
            trimmer=self._usecases.trimmer,
            guard=self._context.guard,
            scope=self._context.scope,
            reporter=self._context.reporter,
        )


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
    context = _RuntimeContext(
        guard=guard,
        scope=scope,
        telemetry=telemetry,
        reporter=reporter,
        bundler=bundler,
        missing_alert=missing_alert,
    )
    assembler = _NavigatorRuntimeAssembler(usecases=usecases, context=context)
    return NavigatorRuntime(
        history=assembler.history(),
        state=assembler.state(),
        tail=assembler.tail(),
    )


__all__ = ["build_navigator_runtime"]

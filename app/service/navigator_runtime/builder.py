"""Factory helpers building the navigator runtime."""
from __future__ import annotations

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
    add_operation = HistoryAddOperation(
        appender=usecases.appender,
        bundler=bundler,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    replace_operation = HistoryReplaceOperation(
        swapper=usecases.swapper,
        bundler=bundler,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    rebase_operation = HistoryRebaseOperation(
        shifter=usecases.shifter,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    back_operation = HistoryBackOperation(
        rewinder=usecases.rewinder,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    trim_operation = HistoryTrimOperation(
        trimmer=usecases.trimmer,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    history = NavigatorHistoryService(
        add=add_operation,
        replace=replace_operation,
        rebase=rebase_operation,
        back=back_operation,
        pop=trim_operation,
    )
    missing_state_alarm = MissingStateAlarm(
        alarm=usecases.alarm,
        scope=scope,
        factory=missing_alert,
    )
    state = NavigatorStateService(
        setter=usecases.setter,
        alarm=usecases.alarm,
        guard=guard,
        scope=scope,
        reporter=reporter,
        missing_alarm=missing_state_alarm,
    )
    tail = NavigatorTail(
        flow=usecases.tailer,
        scope=scope,
        guard=guard,
        telemetry=telemetry,
    )
    return NavigatorRuntime(history=history, state=state, tail=tail)


__all__ = ["build_navigator_runtime"]

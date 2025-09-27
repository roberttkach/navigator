"""Helpers for assembling navigator history services."""
from __future__ import annotations

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope

from .bundler import PayloadBundler
from .contracts import HistoryContracts
from .history import (
    HistoryAddOperation,
    HistoryPayloadAppender,
    HistoryBackOperation,
    HistoryRebaseOperation,
    HistoryReplaceOperation,
    HistoryTrimOperation,
    NavigatorHistoryService,
)
from .reporter import NavigatorReporter


def build_history_service(
    contracts: HistoryContracts,
    *,
    guard: Guardian,
    scope: Scope,
    reporter: NavigatorReporter,
    bundler: PayloadBundler,
) -> NavigatorHistoryService:
    """Compose history operations using dedicated collaborators."""

    payloads = HistoryPayloadAppender(
        appender=contracts.appender,
        bundler=bundler,
    )
    add_operation = HistoryAddOperation(
        payloads=payloads,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    replace_operation = HistoryReplaceOperation(
        swapper=contracts.swapper,
        bundler=bundler,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    rebase_operation = HistoryRebaseOperation(
        shifter=contracts.shifter,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    back_operation = HistoryBackOperation(
        rewinder=contracts.rewinder,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    trim_operation = HistoryTrimOperation(
        trimmer=contracts.trimmer,
        guard=guard,
        scope=scope,
        reporter=reporter,
    )
    return NavigatorHistoryService(
        add=add_operation,
        replace=replace_operation,
        rebase=rebase_operation,
        back=back_operation,
        pop=trim_operation,
    )


__all__ = ["build_history_service"]

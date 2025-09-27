"""Navigator runtime package exposing orchestration helpers."""
from __future__ import annotations

from .api_contracts import (
    NavigatorAssemblyOverrides,
    NavigatorRuntimeBundleLike,
    NavigatorRuntimeInstrument,
)
from .assembly import build_runtime_from_dependencies
from .runtime_factory import build_navigator_runtime
from .contracts import HistoryContracts, NavigatorRuntimeContracts, StateContracts, TailContracts
from navigator.core.contracts.back import NavigatorBackContext, NavigatorBackEvent
from .bundler import PayloadBundler
from .facade import (
    NavigatorFacade,
    NavigatorHistoryFacade,
    NavigatorStateFacade,
    NavigatorTailFacade,
)
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
from .snapshot import NavigatorRuntimeSnapshot
from .state import MissingStateAlarm, NavigatorStateService, StateDescriptor
from .tail import NavigatorTail
from .tail_view import TailView
from .types import MissingAlert
from .usecases import NavigatorUseCases

__all__ = [
    "NavigatorAssemblyOverrides",
    "NavigatorBackContext",
    "NavigatorBackEvent",
    "NavigatorRuntimeInstrument",
    "NavigatorRuntimeBundleLike",
    "build_navigator_runtime",
    "build_runtime_from_dependencies",
    "HistoryAddOperation",
    "HistoryBackOperation",
    "HistoryRebaseOperation",
    "HistoryReplaceOperation",
    "HistoryTrimOperation",
    "HistoryContracts",
    "MissingAlert",
    "NavigatorFacade",
    "NavigatorHistoryFacade",
    "MissingStateAlarm",
    "NavigatorHistoryService",
    "NavigatorStateFacade",
    "NavigatorReporter",
    "NavigatorRuntime",
    "NavigatorTailFacade",
    "NavigatorRuntimeSnapshot",
    "NavigatorRuntimeContracts",
    "NavigatorStateService",
    "NavigatorTail",
    "NavigatorUseCases",
    "PayloadBundler",
    "StateContracts",
    "StateDescriptor",
    "TailContracts",
    "TailView",
]

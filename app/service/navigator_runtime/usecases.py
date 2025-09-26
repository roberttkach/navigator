"""Definitions for navigator use case bundles."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.usecase.alarm import Alarm
from navigator.app.usecase.last import Tailer
from navigator.app.usecase.set import Setter

from .ports import (
    AppendHistoryUseCase,
    RebaseHistoryUseCase,
    ReplaceHistoryUseCase,
    RewindHistoryUseCase,
    TrimHistoryUseCase,
)


@dataclass(frozen=True)
class NavigatorUseCases:
    """Bundle of use cases required to assemble the navigator runtime."""

    appender: AppendHistoryUseCase
    swapper: ReplaceHistoryUseCase
    rewinder: RewindHistoryUseCase
    setter: Setter
    trimmer: TrimHistoryUseCase
    shifter: RebaseHistoryUseCase
    tailer: Tailer
    alarm: Alarm


__all__ = ["NavigatorUseCases"]

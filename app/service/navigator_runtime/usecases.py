"""Definitions for navigator use case bundles."""
from __future__ import annotations

from dataclasses import dataclass

from .ports import (
    AlarmUseCase,
    AppendHistoryUseCase,
    RebaseHistoryUseCase,
    ReplaceHistoryUseCase,
    RewindHistoryUseCase,
    SetStateUseCase,
    TailUseCase,
    TrimHistoryUseCase,
)


@dataclass(frozen=True)
class NavigatorUseCases:
    """Bundle of use cases required to assemble the navigator runtime."""

    appender: AppendHistoryUseCase
    swapper: ReplaceHistoryUseCase
    rewinder: RewindHistoryUseCase
    setter: SetStateUseCase
    trimmer: TrimHistoryUseCase
    shifter: RebaseHistoryUseCase
    tailer: TailUseCase
    alarm: AlarmUseCase


__all__ = ["NavigatorUseCases"]

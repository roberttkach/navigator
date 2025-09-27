"""Contracts describing runtime dependencies for navigator services."""
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
from .usecases import NavigatorUseCases


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

    setter: SetStateUseCase
    alarm: AlarmUseCase


@dataclass(frozen=True)
class TailContracts:
    """Expose tail-specific collaborators required by the runtime."""

    tailer: TailUseCase


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


__all__ = [
    "HistoryContracts",
    "NavigatorRuntimeContracts",
    "StateContracts",
    "TailContracts",
]

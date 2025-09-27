"""Contracts describing runtime dependencies for navigator services."""
from __future__ import annotations

from dataclasses import dataclass

from typing import Protocol

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


class RuntimeContractSource(Protocol):
    """Protocol describing objects capable of resolving runtime contracts."""

    def resolve(self) -> "NavigatorRuntimeContracts":
        """Return contracts that should be used by the runtime."""


@dataclass(frozen=True)
class RuntimeContractSelection(RuntimeContractSource):
    """Capture how runtime contracts should be resolved for assembly."""

    usecases: NavigatorUseCases | None = None
    contracts: "NavigatorRuntimeContracts" | None = None

    def resolve(self) -> "NavigatorRuntimeContracts":
        """Derive runtime contracts from the configured sources."""

        if self.contracts is not None:
            return self.contracts
        if self.usecases is None:
            raise ValueError("either usecases or contracts must be provided")
        return NavigatorRuntimeContracts.from_usecases(self.usecases)


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
    "RuntimeContractSelection",
    "RuntimeContractSource",
    "StateContracts",
    "TailContracts",
]

"""Protocol definitions describing navigator use case contracts."""

from __future__ import annotations

from collections.abc import Sequence
from typing import Any, Protocol

from navigator.core.contracts.back import NavigatorBackContext
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope


class AppendHistoryUseCase(Protocol):
    """Append payloads to history within the supplied scope."""

    async def execute(
        self,
        scope: Scope,
        bundle: Sequence[Payload],
        view: str | None,
        *,
        root: bool = False,
    ) -> None:
        ...


class ReplaceHistoryUseCase(Protocol):
    """Replace existing history entries with freshly rendered payloads."""

    async def execute(self, scope: Scope, bundle: Sequence[Payload]) -> None:
        ...


class RebaseHistoryUseCase(Protocol):
    """Shift the latest marker onto the provided identifier."""

    async def execute(self, marker: int) -> None:
        ...


class RewindHistoryUseCase(Protocol):
    """Navigate backwards in history using optional handler context."""

    async def execute(self, scope: Scope, context: NavigatorBackContext) -> None:
        ...


class TrimHistoryUseCase(Protocol):
    """Reduce history length by the requested amount."""

    async def execute(self, count: int = 1) -> None:
        ...


class SetStateUseCase(Protocol):
    """Restore a state goal for the provided scope."""

    async def execute(self, scope: Scope, goal: str, context: dict[str, Any]) -> None:
        ...


class AlarmUseCase(Protocol):
    """Trigger alert notifications for the supplied scope."""

    async def execute(self, scope: Scope, text: str | None = None) -> None:
        ...


class TailUseCase(Protocol):
    """Coordinate tail operations for conversation history."""

    async def peek(self) -> int | None:
        ...

    async def delete(self, scope: Scope) -> None:
        ...

    async def edit(self, scope: Scope, payload: Payload) -> int | None:
        ...


__all__ = [
    "AppendHistoryUseCase",
    "AlarmUseCase",
    "RebaseHistoryUseCase",
    "ReplaceHistoryUseCase",
    "RewindHistoryUseCase",
    "SetStateUseCase",
    "TailUseCase",
    "TrimHistoryUseCase",
]

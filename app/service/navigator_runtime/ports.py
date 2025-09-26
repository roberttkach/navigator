"""Protocol definitions describing navigator use case contracts."""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from typing import Any, Protocol

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

    async def execute(self, scope: Scope, context: Mapping[str, Any]) -> None:
        ...


class TrimHistoryUseCase(Protocol):
    """Reduce history length by the requested amount."""

    async def execute(self, count: int = 1) -> None:
        ...


__all__ = [
    "AppendHistoryUseCase",
    "RebaseHistoryUseCase",
    "ReplaceHistoryUseCase",
    "RewindHistoryUseCase",
    "TrimHistoryUseCase",
]

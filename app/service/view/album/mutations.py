"""Execute planned album mutations."""

from __future__ import annotations

from typing import Iterable

from navigator.core.value.message import Scope

from ..executor import EditExecutor
from .mutation_plan import AlbumMutation


class AlbumMutationExecutor:
    """Execute album mutations with shared edit executor."""

    def __init__(self, executor: EditExecutor) -> None:
        self._executor = executor

    async def apply(self, scope: Scope, mutations: Iterable[AlbumMutation]) -> bool:
        mutated = False
        for mutation in mutations:
            execution = await self._executor.execute(
                scope,
                mutation.decision,
                mutation.payload,
                mutation.reference,
            )
            mutated = mutated or bool(execution)
        return mutated


__all__ = ["AlbumMutationExecutor"]

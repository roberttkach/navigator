"""Message mutation coordinator for tail operations."""

from __future__ import annotations

from typing import Sequence

from ....core.service.rendering import decision
from ....core.value.message import Scope

from ...service.tail_history import TailHistoryWriter
from ...service.history_mutation import TailHistoryMutator
from ...service.view.executor import EditExecutor
from ...service.view.planner import RenderResult

from .context import TailResolution, TailSnapshot
from .editing import TailEditService, TailFallbackPolicy, TailHistoryPersistence


class MessageEditCoordinator:
    """Coordinate non-inline edits, deletions and resend fallbacks."""

    def __init__(
        self,
        executor: EditExecutor,
        history: TailHistoryWriter,
        mutator: TailHistoryMutator,
        *,
        editing: TailEditService | None = None,
        persistence: TailHistoryPersistence | None = None,
        fallback: TailFallbackPolicy | None = None,
    ) -> None:
        self._editing = editing or TailEditService(executor)
        self._persistence = (
            persistence or TailHistoryPersistence(history=history, mutator=mutator)
        )
        self._fallback = fallback or TailFallbackPolicy()

    async def delete(self, scope: Scope, snapshot: TailSnapshot, *, op: str) -> None:
        """Delete the most recent entry and update history repositories."""

        entry = snapshot.tail
        if entry is None:
            return

        identifiers: list[int] = []
        for message in entry.messages:
            identifiers.append(int(message.id))
            identifiers.extend(int(extra) for extra in (message.extras or []))
        if identifiers:
            await self._editing.executor.delete(scope, identifiers)

        trimmed = snapshot.history[:-1]
        await self._persistence.history.save(trimmed, op=op)
        await self._persistence.history.mark(None, op=op, scope=scope)

    async def edit(
            self,
            scope: Scope,
            snapshot: TailSnapshot,
            resolution: TailResolution,
            *,
            op: str,
    ) -> int | None:
        """Apply message edits or resend fallbacks based on ``resolution``."""

        result = await self._editing.apply(
            scope,
            resolution.decision,
            resolution.payload,
            resolution.base,
        )
        if result:
            await self.persist(snapshot, result, scope=scope, op=op)
            return result.id

        if not self._fallback.allows_resend(resolution, scope):
            return None

        await self._editing.executor.delete(scope, snapshot.targets())
        resend = await self._editing.resend(scope, resolution.payload)
        if resend:
            await self.persist(
                snapshot,
                resend,
                scope=scope,
                op=op,
                extras=[resend.extra],
            )
            return resend.id

        return None

    async def persist(
        self,
        snapshot: TailSnapshot,
        outcome: RenderResult,
        *,
        scope: Scope,
        op: str,
        extras: Sequence[Sequence[int]] | None = None,
    ) -> None:
        await self._persistence.persist(
            snapshot,
            outcome,
            scope=scope,
            op=op,
            extras=extras,
        )


__all__ = ["MessageEditCoordinator"]

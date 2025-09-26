"""Message mutation coordinator for tail operations."""

from __future__ import annotations

from typing import Sequence

from ....core.service.rendering import decision
from ....core.value.message import Scope

from ...service.history_access import TailHistoryTracker
from ...service.history_mutation import TailHistoryMutator
from ...service.view.executor import EditExecutor
from ...service.view.planner import RenderResult

from .context import TailResolution, TailSnapshot


class MessageEditCoordinator:
    """Coordinate non-inline edits, deletions and resend fallbacks."""

    def __init__(
            self,
            executor: EditExecutor,
            history: TailHistoryTracker,
            mutator: TailHistoryMutator,
    ) -> None:
        self._executor = executor
        self._history = history
        self._mutator = mutator

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
            await self._executor.delete(scope, identifiers)

        trimmed = snapshot.history[:-1]
        await self._history.save(trimmed, op=op)
        await self._history.mark(None, op=op, scope=scope)

    async def edit(
            self,
            scope: Scope,
            snapshot: TailSnapshot,
            resolution: TailResolution,
            *,
            op: str,
    ) -> int | None:
        """Apply message edits or resend fallbacks based on ``resolution``."""

        result = await self._apply(scope, resolution.decision, resolution.payload, resolution.base)
        if result:
            await self.persist(snapshot, result, scope=scope, op=op)
            return result.id

        if resolution.decision is decision.Decision.EDIT_TEXT and not (
                resolution.payload.text and str(resolution.payload.text).strip()
        ):
            return None

        if resolution.decision in (
                decision.Decision.EDIT_MEDIA,
                decision.Decision.EDIT_MEDIA_CAPTION,
        ) and not (resolution.payload.media or resolution.payload.group):
            return None

        if scope.inline:
            return None

        if resolution.decision in (
                decision.Decision.EDIT_TEXT,
                decision.Decision.EDIT_MEDIA,
                decision.Decision.EDIT_MEDIA_CAPTION,
                decision.Decision.DELETE_SEND,
        ):
            await self._executor.delete(scope, snapshot.targets())
            resend = await self._apply(
                scope,
                decision.Decision.RESEND,
                resolution.payload,
                None,
            )
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
        index = snapshot.index
        if index is not None and 0 <= index < len(snapshot.history):
            history = snapshot.clone()
            entry = history[index]
            bundle = extras
            if bundle is None and entry.messages:
                mismatch = int(entry.messages[0].id) != int(outcome.id)
                bundle = [outcome.extra] if mismatch else None
            history[index] = self._mutator.reindex(entry, [outcome.id], bundle)
            await self._history.save(history, op=op)
        await self._history.mark(outcome.id, op=op, scope=scope)

    async def _apply(
            self,
            scope: Scope,
            verdict: decision.Decision,
            payload,
            base,
    ) -> RenderResult | None:
        execution = await self._executor.execute(scope, verdict, payload, base)
        if not execution:
            return None
        meta = self._executor.refine(execution, verdict, payload)
        return RenderResult(
            id=execution.result.id,
            extra=list(execution.result.extra),
            meta=meta,
        )


__all__ = ["MessageEditCoordinator"]

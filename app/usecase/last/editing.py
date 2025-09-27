"""Supporting components for tail edit coordination."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Sequence

from ....core.service.rendering import decision
from ....core.value.message import Scope

from ...service.tail_history import TailHistoryWriter
from ...service.history_mutation import TailHistoryMutator
from ...service.view.executor import EditExecutor
from ...service.view.planner import RenderResult

from .context import TailResolution, TailSnapshot


class TailFallbackPolicy:
    """Encapsulate resend eligibility checks."""

    _RESENDABLE = (
        decision.Decision.EDIT_TEXT,
        decision.Decision.EDIT_MEDIA,
        decision.Decision.EDIT_MEDIA_CAPTION,
        decision.Decision.DELETE_SEND,
    )

    def allows_resend(self, resolution: TailResolution, scope: Scope) -> bool:
        """Return ``True`` when resend fallback is permitted."""

        if scope.inline:
            return False
        verdict = resolution.decision
        if verdict not in self._RESENDABLE:
            return False
        payload = resolution.payload
        if verdict is decision.Decision.EDIT_TEXT and not (
            payload.text and str(payload.text).strip()
        ):
            return False
        if verdict in (
            decision.Decision.EDIT_MEDIA,
            decision.Decision.EDIT_MEDIA_CAPTION,
        ) and not (payload.media or payload.group):
            return False
        return True


class TailEditService:
    """Apply edit decisions through the view executor."""

    def __init__(self, executor: EditExecutor) -> None:
        self._executor = executor

    @property
    def executor(self) -> EditExecutor:
        return self._executor

    async def apply(
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

    async def resend(self, scope: Scope, payload) -> RenderResult | None:
        """Apply a resend fallback using ``payload``."""

        return await self.apply(
            scope,
            decision.Decision.RESEND,
            payload,
            None,
        )


@dataclass(slots=True)
class TailHistoryPersistence:
    """Persist updated tail history snapshots."""

    history: TailHistoryWriter
    mutator: TailHistoryMutator

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
            history[index] = self.mutator.reindex(entry, [outcome.id], bundle)
            await self.history.save(history, op=op)
        await self.history.mark(outcome.id, op=op, scope=scope)


__all__ = ["TailEditService", "TailFallbackPolicy", "TailHistoryPersistence"]

"""Synchronize stored ledger messages with desired payloads."""

from __future__ import annotations

from navigator.core.entity.history import Message
from navigator.core.service.rendering import decision
from navigator.core.service.rendering.config import RenderingConfig
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ..executor import EditExecutor
from ..inline import InlineHandler, InlineOutcome

from .models import RenderState


class RenderSynchronizer:
    """Synchronize stored ledger messages with desired payloads."""

    def __init__(
        self,
        executor: EditExecutor,
        inline: InlineHandler,
        rendering: RenderingConfig,
    ) -> None:
        self._executor = executor
        self._inline = inline
        self._rendering = rendering

    async def reconcile(
        self,
        scope: Scope,
        fresh: list[Payload],
        ledger: list[Message],
        state: RenderState,
        *,
        start: int,
        inline_mode: bool,
    ) -> bool:
        mutated = False
        limit = min(len(ledger), len(fresh))
        for index in range(start, limit):
            previous = ledger[index]
            current = fresh[index]
            verdict = decision.decide(previous, current, self._rendering)

            if verdict is decision.Decision.NO_CHANGE:
                state.retain(previous)
                continue

            if inline_mode:
                changed = await self._mediate(scope, current, previous, state)
            else:
                changed = await self._regular(scope, verdict, current, previous, state)

            mutated = mutated or self._retain_if_unchanged(changed, previous, state)

        return mutated

    async def _mediate(
        self,
        scope: Scope,
        payload: Payload,
        previous: Message,
        state: RenderState,
    ) -> bool:
        outcome = await self._inline.handle(
            scope=scope,
            payload=payload,
            tail=previous,
            executor=self._executor,
            config=self._rendering,
        )
        if outcome is None:
            return False
        return self._record(outcome, state)

    async def _regular(
        self,
        scope: Scope,
        verdict: decision.Decision,
        payload: Payload,
        previous: Message,
        state: RenderState,
    ) -> bool:
        execution = await self._executor.execute(scope, verdict, payload, previous)
        if execution is None:
            return False
        meta = self._executor.refine(execution, verdict, payload)
        state.collect(execution, meta)
        return True

    def _record(self, outcome: InlineOutcome, state: RenderState) -> bool:
        meta = self._executor.refine(outcome.execution, outcome.decision, outcome.payload)
        state.collect(outcome.execution, meta)
        return True

    @staticmethod
    def _retain_if_unchanged(
        changed: bool,
        previous: Message,
        state: RenderState,
    ) -> bool:
        if not changed:
            state.retain(previous)
        return changed


__all__ = ["RenderSynchronizer"]


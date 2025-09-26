"""Plan regular rendering flows that may mutate history."""

from __future__ import annotations

from navigator.core.entity.history import Message
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .head import HeadAlignment
from .models import RenderState
from .synchronizer import RenderSynchronizer
from .tails import TailOperations


class RegularRenderPlanner:
    """Plan regular rendering flows that may mutate history."""

    def __init__(
        self,
        head: HeadAlignment,
        synchronizer: RenderSynchronizer,
        tails: TailOperations,
    ) -> None:
        self._head = head
        self._synchronizer = synchronizer
        self._tails = tails

    async def plan(
        self,
        scope: Scope,
        fresh: list[Payload],
        ledger: list[Message],
        state: RenderState,
    ) -> bool:
        origin, head_changed = await self._head.align(scope, ledger, fresh, state)
        mutated = head_changed

        mutated = (
            mutated
            or await self._synchronizer.reconcile(
                scope,
                fresh,
                ledger,
                state,
                start=origin,
                inline_mode=False,
            )
        )

        stored = len(ledger)
        incoming = len(fresh)
        mutated = mutated or await self._tails.trim(scope, ledger, incoming)
        mutated = mutated or await self._tails.append(scope, fresh, stored, state)
        return mutated


__all__ = ["RegularRenderPlanner"]


"""Resolve inline rendering sequences."""

from __future__ import annotations

from navigator.core.entity.history import Message
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .models import RenderState
from .synchronizer import RenderSynchronizer


class InlineRenderPlanner:
    """Resolve inline rendering sequences."""

    def __init__(self, synchronizer: RenderSynchronizer) -> None:
        self._synchronizer = synchronizer

    async def plan(
        self,
        scope: Scope,
        fresh: list[Payload],
        ledger: list[Message],
        state: RenderState,
    ) -> bool:
        return await self._synchronizer.reconcile(
            scope,
            fresh,
            ledger,
            state,
            start=0,
            inline_mode=True,
        )


__all__ = ["InlineRenderPlanner"]


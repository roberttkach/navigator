"""Handle tail trimming and appending of history nodes."""

from __future__ import annotations

from navigator.core.entity.history import Message
from navigator.core.service.rendering import decision
from navigator.core.service.rendering.config import RenderingConfig
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ..executor import EditExecutor

from .models import RenderState


class TailOperations:
    """Handle tail trimming and appending of history nodes."""

    def __init__(self, executor: EditExecutor, rendering: RenderingConfig) -> None:
        self._executor = executor
        self._rendering = rendering

    async def trim(self, scope: Scope, ledger: list[Message], incoming: int) -> bool:
        if len(ledger) <= incoming:
            return False
        targets: list[int] = []
        for message in ledger[incoming:]:
            targets.append(message.id)
            targets.extend(list(message.extras or []))
        if not targets:
            return False
        await self._executor.delete(scope, targets)
        return True

    async def append(
        self,
        scope: Scope,
        fresh: list[Payload],
        stored: int,
        state: RenderState,
    ) -> bool:
        if len(fresh) <= stored:
            return False
        mutated = False
        for payload in fresh[stored:]:
            verdict = decision.decide(None, payload, self._rendering)
            execution = await self._executor.execute(scope, verdict, payload, None)
            if not execution:
                continue
            meta = self._executor.refine(execution, verdict, payload)
            state.collect(execution, meta)
            mutated = True
        return mutated


__all__ = ["TailOperations"]


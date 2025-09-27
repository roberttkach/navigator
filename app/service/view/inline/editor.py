from __future__ import annotations

from navigator.core.entity.history import Message
from navigator.core.service.rendering import decision as D
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ..executor import EditExecutor, Execution
from .outcome import InlineOutcome


class InlineEditor:
    """Apply inline decisions through the message gateway executor."""

    async def apply(
            self,
            scope: Scope,
            verdict: D.Decision,
            payload: Payload,
            base: Message | None,
            *,
            executor: EditExecutor,
    ) -> InlineOutcome | None:
        execution = await executor.execute(scope, verdict, payload, base)
        if execution is None:
            return None
        return InlineOutcome(execution=execution, decision=verdict, payload=payload)


__all__ = ["InlineEditor", "InlineOutcome"]

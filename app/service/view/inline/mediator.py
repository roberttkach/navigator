"""Mediators coordinating inline edit execution."""
from __future__ import annotations

from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .editor import InlineEditor, InlineOutcome
from ..executor import EditExecutor


class InlineEditMediator:
    """Delegate inline edits to the executor with consistent wiring."""

    def __init__(self, editor: InlineEditor) -> None:
        self._editor = editor

    async def apply(
        self,
        scope: Scope,
        verdict: "D.Decision",
        payload: Payload,
        base: "Message" | None,
        *,
        executor: EditExecutor,
    ) -> InlineOutcome | None:
        from navigator.core.service.rendering import decision as D
        from navigator.core.entity.history import Message

        return await self._editor.apply(
            scope,
            verdict,
            payload,
            base,
            executor=executor,
        )


__all__ = ["InlineEditMediator"]

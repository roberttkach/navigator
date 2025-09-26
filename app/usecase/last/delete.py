"""Workflow dedicated to tail delete operations."""

from __future__ import annotations

from navigator.core.value.message import Scope

from ...service.history_access import TailHistoryTracker
from .context import TailSnapshot, TailTelemetry
from .mutation import MessageEditCoordinator


class TailDeleteWorkflow:
    """Handle deletion of the most recent navigator history entry."""

    def __init__(
        self,
        *,
        history: TailHistoryTracker,
        mutation: MessageEditCoordinator,
        telemetry: TailTelemetry,
        op: str = "last.delete",
    ) -> None:
        self._history = history
        self._mutation = mutation
        self._telemetry = telemetry
        self._op = op

    async def execute(self, scope: Scope) -> None:
        history = await self._history.load(scope)
        if not history:
            self._telemetry.skip(op=self._op, note="no_history")
            return

        if scope.inline and not getattr(scope, "business", False):
            await self._history.trim_inline(history, scope, op=self._op)
            return

        marker = await self._history.peek()
        snapshot = TailSnapshot.build(marker, history)
        await self._mutation.delete(scope, snapshot, op=self._op)


__all__ = ["TailDeleteWorkflow"]

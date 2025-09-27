"""Workflow dedicated to tail edit operations."""

from __future__ import annotations

from typing import Optional

from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ...service.tail_history import TailHistoryReader
from .context import TailDecisionService, TailSnapshot, TailTelemetry
from .inline import InlineEditCoordinator
from .mutation import MessageEditCoordinator


class TailEditWorkflow:
    """Handle editing of the most recent navigator history entry."""

    def __init__(
        self,
        *,
        reader: TailHistoryReader,
        decision: TailDecisionService,
        inline: InlineEditCoordinator,
        mutation: MessageEditCoordinator,
        telemetry: TailTelemetry,
        op: str = "last.edit",
    ) -> None:
        self._reader = reader
        self._decision = decision
        self._inline = inline
        self._mutation = mutation
        self._telemetry = telemetry
        self._op = op

    async def execute(self, scope: Scope, payload: Payload) -> Optional[int]:
        marker = await self._reader.peek()
        if not marker:
            self._telemetry.skip(op=self._op, note="no_last_id")
            return None

        history = await self._reader.load(scope)
        snapshot = TailSnapshot.build(marker, history)

        resolution = self._decision.resolve(scope, payload, snapshot)
        if resolution is None:
            return None

        if scope.inline:
            result = await self._inline.apply(scope, snapshot, resolution)
            if not result:
                return None
            await self._mutation.persist(
                snapshot,
                result,
                scope=scope,
                op=self._op,
            )
            return result.id

        return await self._mutation.edit(
            scope,
            snapshot,
            resolution,
            op=self._op,
        )


__all__ = ["TailEditWorkflow"]

"""Tail use-case orchestration based on dedicated services."""

from __future__ import annotations

from typing import Optional

from ....core.value.content import Payload
from ....core.value.message import Scope

from ...service.history_access import TailHistoryAccess
from .context import TailDecisionService, TailSnapshot, TailTelemetry
from .inline import InlineEditCoordinator
from .mutation import MessageEditCoordinator


class Tailer:
    """Coordinate tail operations across dedicated collaborators."""

    _OP_DELETE = "last.delete"
    _OP_EDIT = "last.edit"

    def __init__(
            self,
            history: TailHistoryAccess,
            decision: TailDecisionService,
            inline: InlineEditCoordinator,
            mutation: MessageEditCoordinator,
            telemetry: TailTelemetry,
    ) -> None:
        self._history = history
        self._decision = decision
        self._inline = inline
        self._mutation = mutation
        self._telemetry = telemetry

    async def peek(self) -> Optional[int]:
        """Return the most recent marker identifier."""

        return await self._history.peek()

    async def delete(self, scope: Scope) -> None:
        """Delete the most recent history entry for ``scope``."""

        history = await self._history.load(scope)
        if not history:
            self._telemetry.skip(op=self._OP_DELETE, note="no_history")
            return

        if scope.inline and not getattr(scope, "business", False):
            await self._history.trim_inline(history, scope, op=self._OP_DELETE)
            return

        marker = await self._history.peek()
        snapshot = TailSnapshot.build(marker, history)
        await self._mutation.delete(scope, snapshot, op=self._OP_DELETE)

    async def edit(self, scope: Scope, payload: Payload) -> Optional[int]:
        """Edit the most recent message according to ``payload``."""

        marker = await self._history.peek()
        if not marker:
            self._telemetry.skip(op=self._OP_EDIT, note="no_last_id")
            return None

        history = await self._history.load(scope)
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
                op=self._OP_EDIT,
            )
            return result.id

        return await self._mutation.edit(
            scope,
            snapshot,
            resolution,
            op=self._OP_EDIT,
        )


__all__ = ["Tailer"]

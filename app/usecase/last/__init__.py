"""Tail use-case orchestration based on dedicated services."""

from __future__ import annotations

from typing import Optional

from ....core.value.content import Payload
from ....core.value.message import Scope

from ...service.history_access import TailHistoryTracker
from .delete import TailDeleteWorkflow
from .edit import TailEditWorkflow


class Tailer:
    """Coordinate tail operations across dedicated collaborators."""

    def __init__(
        self,
        history: TailHistoryTracker,
        *,
        delete: TailDeleteWorkflow,
        edit: TailEditWorkflow,
    ) -> None:
        self._history = history
        self._delete = delete
        self._edit = edit

    async def peek(self) -> Optional[int]:
        """Return the most recent marker identifier."""

        return await self._history.peek()

    async def delete(self, scope: Scope) -> None:
        """Delete the most recent history entry for ``scope``."""

        await self._delete.execute(scope)

    async def edit(self, scope: Scope, payload: Payload) -> Optional[int]:
        """Edit the most recent message according to ``payload``."""

        return await self._edit.execute(scope, payload)


__all__ = ["Tailer"]

"""Inline coordination helpers for tail edits."""

from __future__ import annotations

from ....core.service.rendering.config import RenderingConfig
from ....core.value.message import Scope

from ...service.view.executor import EditExecutor
from ...service.view.inline import InlineHandler
from ...service.view.planner import RenderResult

from .context import TailResolution, TailSnapshot


class InlineEditCoordinator:
    """Coordinate inline editing workflow for the tail use-case."""

    def __init__(
            self,
            handler: InlineHandler,
            executor: EditExecutor,
            rendering: RenderingConfig,
    ) -> None:
        self._handler = handler
        self._executor = executor
        self._rendering = rendering

    async def apply(
            self,
            scope: Scope,
            snapshot: TailSnapshot,
            resolution: TailResolution,
    ) -> RenderResult | None:
        """Execute inline reconciliation for ``resolution``."""

        base = resolution.base
        head = base.messages[0] if base and base.messages else None
        outcome = await self._handler.handle(
            scope=scope,
            payload=resolution.payload,
            tail=head,
            executor=self._executor,
            config=self._rendering,
        )
        if not outcome:
            return None
        return self._result(outcome.execution, outcome.decision, outcome.payload)

    def _result(self, execution, verdict, payload) -> RenderResult:
        meta = self._executor.refine(execution, verdict, payload)
        return RenderResult(
            id=execution.result.id,
            extra=list(execution.result.extra),
            meta=meta,
        )


__all__ = ["InlineEditCoordinator"]

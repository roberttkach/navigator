"""Workflow runner coordinating retreat execution."""
from __future__ import annotations

from collections.abc import Mapping

from aiogram.types import CallbackQuery

from .failures import RetreatFailurePolicy
from .protocols import NavigatorBack
from .result import RetreatResult
from .workflow import RetreatWorkflow


class RetreatWorkflowRunner:
    """Execute workflow logic while delegating failure handling."""

    def __init__(self, workflow: RetreatWorkflow, failures: RetreatFailurePolicy) -> None:
        self._workflow = workflow
        self._failures = failures

    async def run(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: Mapping[str, object],
    ) -> RetreatResult:
        try:
            return await self._workflow.execute(cb, navigator, payload)
        except Exception as error:  # pragma: no cover - defensive net for logging
            return self._failures.handle(error)


__all__ = ["RetreatWorkflowRunner"]

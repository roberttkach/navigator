"""Telemetry-aware orchestration for retreat workflows."""
from __future__ import annotations

from collections.abc import Mapping

from aiogram.types import CallbackQuery

from .protocols import NavigatorBack
from .reporting import RetreatOutcomeReporter
from .result import RetreatResult
from .runner import RetreatWorkflowRunner
from .session import TelemetryScopeFactory


class RetreatOrchestrator:
    """Drive retreat workflow execution with dedicated collaborators."""

    def __init__(
        self,
        *,
        telemetry: TelemetryScopeFactory,
        runner: RetreatWorkflowRunner,
        reporter: RetreatOutcomeReporter,
    ) -> None:
        self._telemetry = telemetry
        self._runner = runner
        self._reporter = reporter

    async def execute(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: Mapping[str, object],
    ) -> RetreatResult:
        session = self._telemetry.start(cb)
        result = await self._runner.run(cb, navigator, payload)
        return self._reporter.report(result, session)


__all__ = ["RetreatOrchestrator"]

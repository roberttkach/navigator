"""Adapters exposing telegram retreat orchestration."""

from __future__ import annotations

from aiogram.types import CallbackQuery

from navigator.app.service.retreat_failure import RetreatFailureResolver
from navigator.core.telemetry import Telemetry

from .context import RetreatContextBuilder
from .orchestrator import RetreatOrchestrator
from .outcome import RetreatOutcome, RetreatOutcomeFactory
from .protocols import NavigatorBack, Translator
from .telemetry import RetreatTelemetry
from .workflow import RetreatWorkflow


class RetreatHandler:
    """Adapt retreat workflow results to Telegram specific outcomes."""

    def __init__(
        self,
        orchestrator: RetreatOrchestrator,
        outcomes: RetreatOutcomeFactory,
    ) -> None:
        self._orchestrator = orchestrator
        self._outcomes = outcomes

    async def __call__(
        self,
        cb: CallbackQuery,
        navigator: NavigatorBack,
        payload: dict[str, object],
    ) -> RetreatOutcome:
        result = await self._orchestrator.execute(cb, navigator, payload)
        return self._outcomes.render(result, cb)


def create_retreat_handler(telemetry: Telemetry, translator: Translator) -> RetreatHandler:
    """Return a retreat handler with default orchestration components."""

    instrumentation = RetreatTelemetry(telemetry)
    context = RetreatContextBuilder()
    failures = RetreatFailureResolver()
    workflow = RetreatWorkflow(context=context, failures=failures)
    orchestrator = RetreatOrchestrator(telemetry=instrumentation, workflow=workflow)
    outcomes = RetreatOutcomeFactory(translator)
    return RetreatHandler(orchestrator=orchestrator, outcomes=outcomes)


__all__ = ["RetreatHandler", "create_retreat_handler"]

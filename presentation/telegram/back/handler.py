"""Adapters exposing telegram retreat orchestration."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

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
        payload: dict[str, Any],
    ) -> RetreatOutcome:
        result = await self._orchestrator.execute(cb, navigator, payload)
        return self._outcomes.render(result, cb)


@dataclass(slots=True)
class RetreatHandlerBuilder:
    """Assemble retreat handlers while allowing dependency overrides."""

    telemetry: Telemetry
    translator: Translator
    context: RetreatContextBuilder | None = None
    failures: RetreatFailureResolver | None = None
    workflow: RetreatWorkflow | None = None
    orchestrator: RetreatOrchestrator | None = None
    outcomes: RetreatOutcomeFactory | None = None
    instrumentation: RetreatTelemetry | None = None

    def build(self) -> RetreatHandler:
        context = self.context or RetreatContextBuilder()
        failures = self.failures or RetreatFailureResolver()
        workflow = self.workflow or RetreatWorkflow(context=context, failures=failures)
        instrumentation = self.instrumentation or RetreatTelemetry(self.telemetry)
        orchestrator = self.orchestrator or RetreatOrchestrator(
            telemetry=instrumentation,
            workflow=workflow,
        )
        outcomes = self.outcomes or RetreatOutcomeFactory(self.translator)
        return RetreatHandler(orchestrator=orchestrator, outcomes=outcomes)


def create_retreat_handler(
    telemetry: Telemetry,
    translator: Translator,
    *,
    context: RetreatContextBuilder | None = None,
    failures: RetreatFailureResolver | None = None,
    workflow: RetreatWorkflow | None = None,
    orchestrator: RetreatOrchestrator | None = None,
    outcomes: RetreatOutcomeFactory | None = None,
    instrumentation: RetreatTelemetry | None = None,
) -> RetreatHandler:
    """Return a retreat handler built from configurable components."""

    builder = RetreatHandlerBuilder(
        telemetry=telemetry,
        translator=translator,
        context=context,
        failures=failures,
        workflow=workflow,
        orchestrator=orchestrator,
        outcomes=outcomes,
        instrumentation=instrumentation,
    )
    return builder.build()


__all__ = ["RetreatHandler", "create_retreat_handler"]

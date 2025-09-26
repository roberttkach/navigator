"""Adapters exposing telegram retreat orchestration."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Callable

from aiogram.types import CallbackQuery

from navigator.app.service.retreat_failure import RetreatFailureResolver
from navigator.core.telemetry import Telemetry

from .context import RetreatContextBuilder
from .orchestrator import RetreatOrchestrator
from .outcome import RetreatOutcome, RetreatOutcomeFactory
from .protocols import NavigatorBack, Translator
from .telemetry import RetreatTelemetry
from .workflow import RetreatWorkflow


@dataclass(frozen=True, slots=True)
class RetreatHandlerProviders:
    """Factory hooks for assembling retreat handler dependencies."""

    context: Callable[[], RetreatContextBuilder] = RetreatContextBuilder
    failures: Callable[[], RetreatFailureResolver] = RetreatFailureResolver
    workflow: Callable[[RetreatContextBuilder, RetreatFailureResolver], RetreatWorkflow] = (
        lambda context, failures: RetreatWorkflow(context=context, failures=failures)
    )
    instrumentation: Callable[[Telemetry], RetreatTelemetry] = (
        lambda telemetry: RetreatTelemetry(telemetry)
    )
    orchestrator: Callable[[RetreatTelemetry, RetreatWorkflow], RetreatOrchestrator] = (
        lambda instrumentation, workflow: RetreatOrchestrator(
            telemetry=instrumentation,
            workflow=workflow,
        )
    )
    outcomes: Callable[[Translator], RetreatOutcomeFactory] = (
        lambda translator: RetreatOutcomeFactory(translator)
    )


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
    providers: RetreatHandlerProviders = field(default_factory=RetreatHandlerProviders)
    context: RetreatContextBuilder | None = None
    failures: RetreatFailureResolver | None = None
    workflow: RetreatWorkflow | None = None
    orchestrator: RetreatOrchestrator | None = None
    outcomes: RetreatOutcomeFactory | None = None
    instrumentation: RetreatTelemetry | None = None

    def build(self) -> RetreatHandler:
        providers = self.providers
        context = self.context or providers.context()
        failures = self.failures or providers.failures()
        workflow = self.workflow or providers.workflow(context, failures)
        instrumentation = self.instrumentation
        if self.orchestrator is None:
            instrumentation = instrumentation or providers.instrumentation(self.telemetry)
            orchestrator = providers.orchestrator(instrumentation, workflow)
        else:
            orchestrator = self.orchestrator
        outcomes = self.outcomes or providers.outcomes(self.translator)
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


__all__ = ["RetreatHandler", "RetreatHandlerBuilder", "RetreatHandlerProviders", "create_retreat_handler"]

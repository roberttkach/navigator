"""Factories assembling retreat handlers with dependency overrides."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Callable

from navigator.app.service.retreat_failure import RetreatFailureResolver
from navigator.core.telemetry import Telemetry

from .context import RetreatContextBuilder
from .handler import RetreatHandler
from .orchestrator import RetreatOrchestrator
from .outcome import RetreatOutcomeFactory
from .protocols import Translator
from .telemetry import RetreatTelemetry
from .workflow import RetreatWorkflow


@dataclass(frozen=True, slots=True)
class RetreatHandlerProviders:
    """Expose hooks to lazily create retreat handler collaborators."""

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


@dataclass(frozen=True, slots=True)
class RetreatHandlerOverrides:
    """Optional dependencies that may replace individual collaborators."""

    context: RetreatContextBuilder | None = None
    failures: RetreatFailureResolver | None = None
    workflow: RetreatWorkflow | None = None
    instrumentation: RetreatTelemetry | None = None
    orchestrator: RetreatOrchestrator | None = None
    outcomes: RetreatOutcomeFactory | None = None


@dataclass(slots=True)
class RetreatHandlerFactory:
    """Create retreat handlers while isolating assembly responsibilities."""

    telemetry: Telemetry
    translator: Translator
    providers: RetreatHandlerProviders = field(default_factory=RetreatHandlerProviders)

    def create(
        self, overrides: RetreatHandlerOverrides | None = None
    ) -> RetreatHandler:
        options = overrides or RetreatHandlerOverrides()
        providers = self.providers

        context = options.context or providers.context()
        failures = options.failures or providers.failures()
        workflow = options.workflow or providers.workflow(context, failures)

        if options.orchestrator is None:
            instrumentation = (
                options.instrumentation
                or providers.instrumentation(self.telemetry)
            )
            orchestrator = providers.orchestrator(instrumentation, workflow)
        else:
            orchestrator = options.orchestrator

        outcomes = options.outcomes or providers.outcomes(self.translator)
        return RetreatHandler(orchestrator=orchestrator, outcomes=outcomes)


def create_retreat_handler(
    telemetry: Telemetry,
    translator: Translator,
    *,
    overrides: RetreatHandlerOverrides | None = None,
    providers: RetreatHandlerProviders | None = None,
) -> RetreatHandler:
    """Convenience wrapper returning an assembled retreat handler."""

    factory = RetreatHandlerFactory(
        telemetry=telemetry,
        translator=translator,
        providers=providers or RetreatHandlerProviders(),
    )
    return factory.create(overrides)


__all__ = [
    "RetreatHandlerFactory",
    "RetreatHandlerOverrides",
    "RetreatHandlerProviders",
    "create_retreat_handler",
]


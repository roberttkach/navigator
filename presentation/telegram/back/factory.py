"""Factories assembling retreat handlers with dependency overrides."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

from navigator.core.telemetry import Telemetry

from .context import RetreatContextBuilder
from .handler import RetreatHandler
from .orchestrator import RetreatOrchestrator
from .outcome import RetreatOutcomeFactory
from .protocols import Translator
from .telemetry import RetreatTelemetry

if TYPE_CHECKING:
    from navigator.app.service.retreat_failure import RetreatFailureResolver
    from .workflow import RetreatWorkflow


@dataclass(frozen=True, slots=True)
class RetreatHandlerProviders:
    """Expose hooks to lazily create retreat handler collaborators."""

    context: Callable[[], RetreatContextBuilder]
    failures: Callable[[], "RetreatFailureResolver"]
    workflow: Callable[[RetreatContextBuilder, "RetreatFailureResolver"], "RetreatWorkflow"]
    instrumentation: Callable[[Telemetry], RetreatTelemetry]
    orchestrator: Callable[[RetreatTelemetry, "RetreatWorkflow"], RetreatOrchestrator]
    outcomes: Callable[[Translator], RetreatOutcomeFactory]


@dataclass(frozen=True, slots=True)
class RetreatHandlerOverrides:
    """Optional dependencies that may replace individual collaborators."""

    context: RetreatContextBuilder | None = None
    failures: "RetreatFailureResolver" | None = None
    workflow: "RetreatWorkflow" | None = None
    instrumentation: RetreatTelemetry | None = None
    orchestrator: RetreatOrchestrator | None = None
    outcomes: RetreatOutcomeFactory | None = None


@dataclass(slots=True)
class RetreatHandlerFactory:
    """Create retreat handlers while isolating assembly responsibilities."""

    telemetry: Telemetry
    translator: Translator
    providers: RetreatHandlerProviders

    def create(
        self,
        *,
        overrides: RetreatHandlerOverrides | None = None,
    ) -> RetreatHandler:
        options = overrides or RetreatHandlerOverrides()
        providers = self.providers

        context = options.context or providers.context()
        failures = options.failures or providers.failures()
        workflow = options.workflow or providers.workflow(context, failures)

        if options.orchestrator is None:
            instrumentation = (
                options.instrumentation or providers.instrumentation(self.telemetry)
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
    providers: RetreatHandlerProviders,
    overrides: RetreatHandlerOverrides | None = None,
) -> RetreatHandler:
    """Convenience wrapper returning an assembled retreat handler."""

    factory = RetreatHandlerFactory(
        telemetry=telemetry,
        translator=translator,
        providers=providers,
    )
    return factory.create(overrides=overrides)


__all__ = [
    "RetreatHandlerFactory",
    "RetreatHandlerOverrides",
    "RetreatHandlerProviders",
    "create_retreat_handler",
]

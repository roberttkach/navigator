"""Factories assembling retreat handlers with dependency overrides."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

from navigator.core.telemetry import Telemetry

from .context import RetreatContextBuilder
from .handler import RetreatHandler
from .orchestrator import RetreatOrchestrator
from .outcome import RetreatOutcomeFactory
from .protocols import RetreatFailureTranslator, Translator
from .telemetry import RetreatTelemetry

if TYPE_CHECKING:
    from .workflow import RetreatWorkflow


@dataclass(frozen=True, slots=True)
class RetreatHandlerProviders:
    """Expose hooks to lazily create retreat handler collaborators."""

    context: Callable[[], RetreatContextBuilder]
    failures: Callable[[], RetreatFailureTranslator]
    workflow: Callable[[RetreatContextBuilder, RetreatFailureTranslator], "RetreatWorkflow"]
    instrumentation: Callable[[Telemetry], RetreatTelemetry]
    orchestrator: Callable[[RetreatTelemetry, "RetreatWorkflow"], RetreatOrchestrator]
    outcomes: Callable[[Translator], RetreatOutcomeFactory]


@dataclass(frozen=True, slots=True)
class RetreatHandlerOverrides:
    """Optional dependencies that may replace individual collaborators."""

    context: RetreatContextBuilder | None = None
    failures: RetreatFailureTranslator | None = None
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

        bundle = RetreatWorkflowBundle.from_overrides(options, providers)
        resolution = RetreatHandlerResolution(
            telemetry=self.telemetry,
            translator=self.translator,
            providers=providers,
            overrides=options,
        )
        orchestrator = resolution.resolve_orchestrator(bundle)
        outcomes = resolution.resolve_outcomes()
        return RetreatHandler(orchestrator=orchestrator, outcomes=outcomes)


@dataclass(frozen=True, slots=True)
class RetreatWorkflowBundle:
    """Capture the workflow-related collaborators for handler assembly."""

    context: RetreatContextBuilder
    failures: RetreatFailureTranslator
    workflow: "RetreatWorkflow"

    @classmethod
    def from_overrides(
        cls,
        overrides: RetreatHandlerOverrides,
        providers: RetreatHandlerProviders,
    ) -> "RetreatWorkflowBundle":
        """Resolve workflow collaborators using overrides when present."""

        context = overrides.context or providers.context()
        failures = overrides.failures or providers.failures()
        workflow = overrides.workflow or providers.workflow(context, failures)
        return cls(context=context, failures=failures, workflow=workflow)


@dataclass(slots=True)
class RetreatHandlerResolution:
    """Resolve orchestration and outcome collaborators for the handler."""

    telemetry: Telemetry
    translator: Translator
    providers: RetreatHandlerProviders
    overrides: RetreatHandlerOverrides

    def resolve_orchestrator(
        self, bundle: RetreatWorkflowBundle
    ) -> RetreatOrchestrator:
        """Build the orchestrator honoring optional overrides."""

        if self.overrides.orchestrator is not None:
            return self.overrides.orchestrator
        instrumentation = self.overrides.instrumentation or self.providers.instrumentation(
            self.telemetry
        )
        return self.providers.orchestrator(instrumentation, bundle.workflow)

    def resolve_outcomes(self) -> RetreatOutcomeFactory:
        """Build the outcome factory honoring optional overrides."""

        if self.overrides.outcomes is not None:
            return self.overrides.outcomes
        return self.providers.outcomes(self.translator)


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

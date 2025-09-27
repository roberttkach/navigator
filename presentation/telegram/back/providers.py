"""Default providers bridging presentation layer with application services."""

from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from navigator.core.telemetry import Telemetry

from .assembly import RetreatHandlerProviders
from .context import RetreatContextBuilder
from .failures import RetreatFailurePolicy
from .orchestrator import RetreatOrchestrator
from .reporting import RetreatOutcomeReporter
from .runner import RetreatWorkflowRunner
from .session import TelemetryScopeFactory
from .outcome import RetreatOutcomeFactory
from .protocols import RetreatFailureNotes, RetreatFailureTranslator, Translator
from .telemetry import RetreatTelemetry
from .workflow import RetreatWorkflow


@dataclass(frozen=True)
class RetreatOrchestratorFactory:
    """Create orchestrators while abstracting concrete implementations."""

    telemetry_factory: Callable[[RetreatTelemetry], TelemetryScopeFactory]
    failure_policy_factory: Callable[[], RetreatFailurePolicy]
    runner_factory: Callable[
        [RetreatWorkflow, RetreatFailurePolicy], RetreatWorkflowRunner
    ]
    reporter_factory: Callable[[], RetreatOutcomeReporter]

    def create(
        self, instrumentation: RetreatTelemetry, workflow: RetreatWorkflow
    ) -> RetreatOrchestrator:
        """Build an orchestrator using configured collaborators."""

        policy = self.failure_policy_factory()
        telemetry = self.telemetry_factory(instrumentation)
        runner = self.runner_factory(workflow, policy)
        reporter = self.reporter_factory()
        return RetreatOrchestrator(
            telemetry=telemetry,
            runner=runner,
            reporter=reporter,
        )


@dataclass(frozen=True)
class RetreatWorkflowModule:
    """Provide factories building workflow-related collaborators."""

    context_factory: Callable[[], RetreatContextBuilder]

    def context(self) -> RetreatContextBuilder:
        return self.context_factory()

    def workflow(
        self, context: RetreatContextBuilder, failures: RetreatFailureTranslator
    ) -> RetreatWorkflow:
        return RetreatWorkflow.from_builders(context=context, failures=failures)


@dataclass(frozen=True)
class RetreatInstrumentationModule:
    """Produce telemetry wrappers for retreat workflows."""

    def build(self, telemetry: Telemetry) -> RetreatTelemetry:
        return RetreatTelemetry(telemetry)


@dataclass(frozen=True)
class RetreatOutcomeModule:
    """Create factories translating retreat outcomes."""

    notes_factory: Callable[[], RetreatFailureNotes]

    def build(self, translator: Translator) -> RetreatOutcomeFactory:
        return RetreatOutcomeFactory(translator, self.notes_factory())


@dataclass(frozen=True)
class RetreatProviderCatalog:
    """Aggregate factory functions used to construct retreat handlers."""

    failures: Callable[[], RetreatFailureTranslator]
    orchestrators: RetreatOrchestratorFactory
    workflow: RetreatWorkflowModule
    instrumentation: RetreatInstrumentationModule
    outcomes: RetreatOutcomeModule

    def build(self) -> RetreatHandlerProviders:
        """Produce fully configured handler providers."""

        return RetreatHandlerProviders(
            context=self.workflow.context,
            failures=self.failures,
            workflow=self.workflow.workflow,
            instrumentation=self.instrumentation.build,
            orchestrator=self.orchestrators.create,
            outcomes=self.outcomes.build,
        )


def create_retreat_orchestrator_factory() -> RetreatOrchestratorFactory:
    """Construct a retreat orchestrator factory with default policies."""

    return RetreatOrchestratorFactory(
        telemetry_factory=TelemetryScopeFactory,
        failure_policy_factory=RetreatFailurePolicy,
        runner_factory=lambda workflow, policy: RetreatWorkflowRunner(workflow, policy),
        reporter_factory=RetreatOutcomeReporter,
    )


def default_retreat_providers(
    *,
    failures: Callable[[], RetreatFailureTranslator],
    notes: Callable[[], RetreatFailureNotes],
) -> RetreatHandlerProviders:
    """Return providers wiring application services for retreat handling."""

    catalog = RetreatProviderCatalog(
        failures=failures,
        orchestrators=create_retreat_orchestrator_factory(),
        workflow=RetreatWorkflowModule(RetreatContextBuilder),
        instrumentation=RetreatInstrumentationModule(),
        outcomes=RetreatOutcomeModule(notes),
    )
    return catalog.build()


__all__ = [
    "RetreatOrchestratorFactory",
    "RetreatProviderCatalog",
    "create_retreat_orchestrator_factory",
    "default_retreat_providers",
]

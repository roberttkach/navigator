"""Default providers bridging presentation layer with application services."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from navigator.core.telemetry import Telemetry

from .assembly import RetreatHandlerProviders
from .context import RetreatContextBuilder
from .failures import RetreatFailurePolicy
from .orchestrator import RetreatOrchestrator
from .outcome import RetreatOutcomeFactory
from .protocols import RetreatFailureNotes, RetreatFailureTranslator, Translator
from .reporting import RetreatOutcomeReporter
from .runner import RetreatWorkflowRunner
from .session import TelemetryScopeFactory
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
class RetreatWorkflowProvidersFactory:
    """Compose workflow related providers without touching orchestrators."""

    module: RetreatWorkflowModule

    def create(
        self,
        failures: Callable[[], RetreatFailureTranslator],
    ) -> tuple[
        Callable[[], RetreatContextBuilder],
        Callable[[], RetreatFailureTranslator],
        Callable[[RetreatContextBuilder, RetreatFailureTranslator], RetreatWorkflow],
    ]:
        return (self.module.context, failures, self.module.workflow)


@dataclass(frozen=True)
class RetreatOrchestratorProvidersFactory:
    """Keep orchestration composition separate from workflow creation."""

    factory: RetreatOrchestratorFactory
    instrumentation: RetreatInstrumentationModule

    def create(
        self,
    ) -> tuple[
        Callable[[Telemetry], RetreatTelemetry],
        Callable[[RetreatTelemetry, RetreatWorkflow], RetreatOrchestrator],
    ]:
        return (self.instrumentation.build, self.factory.create)


@dataclass(frozen=True)
class RetreatOutcomeProvidersFactory:
    """Expose only the outcome providers assembly responsibilities."""

    module: RetreatOutcomeModule

    def create(self) -> Callable[[Translator], RetreatOutcomeFactory]:
        return self.module.build


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

    workflow_factory = RetreatWorkflowProvidersFactory(
        module=RetreatWorkflowModule(RetreatContextBuilder),
    )
    context_provider, failure_provider, workflow_provider = workflow_factory.create(
        failures
    )
    orchestrator_factory = RetreatOrchestratorProvidersFactory(
        factory=create_retreat_orchestrator_factory(),
        instrumentation=RetreatInstrumentationModule(),
    )
    instrumentation_provider, orchestrator_provider = orchestrator_factory.create()
    outcome_factory = RetreatOutcomeProvidersFactory(
        module=RetreatOutcomeModule(notes),
    )
    return RetreatHandlerProviders(
        context=context_provider,
        failures=failure_provider,
        workflow=workflow_provider,
        instrumentation=instrumentation_provider,
        orchestrator=orchestrator_provider,
        outcomes=outcome_factory.create(),
    )


__all__ = [
    "RetreatOrchestratorFactory",
    "RetreatOrchestratorProvidersFactory",
    "RetreatOutcomeModule",
    "RetreatOutcomeProvidersFactory",
    "RetreatWorkflowModule",
    "RetreatWorkflowProvidersFactory",
    "create_retreat_orchestrator_factory",
    "default_retreat_providers",
]

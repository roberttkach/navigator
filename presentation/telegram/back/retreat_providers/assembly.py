"""High level assembly helpers for retreat handler providers."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..assembly.providers import RetreatHandlerProviders
from ..context import RetreatContextBuilder
from ..protocols import RetreatFailureNotes, RetreatFailureTranslator
from .instrumentation import RetreatInstrumentationModule
from .orchestrator import (
    RetreatOrchestratorFactory,
    RetreatOrchestratorProvidersFactory,
    create_retreat_orchestrator_factory,
)
from .outcome import RetreatOutcomeModule, RetreatOutcomeProvidersFactory
from .workflow import RetreatWorkflowModule, RetreatWorkflowProvidersFactory


@dataclass(frozen=True, slots=True)
class RetreatProviderModules:
    """Group modules used to compose retreat handler providers."""

    workflow: RetreatWorkflowModule
    orchestrator: RetreatOrchestratorFactory
    instrumentation: RetreatInstrumentationModule
    outcome: RetreatOutcomeModule


@dataclass(frozen=True)
class RetreatProviderModuleFactory:
    """Build provider modules without coupling assembly to defaults."""

    notes: Callable[[], RetreatFailureNotes]
    context_factory: Callable[[], RetreatContextBuilder] = RetreatContextBuilder
    orchestrator_factory: RetreatOrchestratorFactory | None = None
    instrumentation: RetreatInstrumentationModule | None = None

    def create(self) -> RetreatProviderModules:
        """Create a configured set of modules for provider assembly."""

        return RetreatProviderModules(
            workflow=RetreatWorkflowModule(self.context_factory),
            orchestrator=self.orchestrator_factory or create_retreat_orchestrator_factory(),
            instrumentation=self.instrumentation or RetreatInstrumentationModule(),
            outcome=RetreatOutcomeModule(self.notes),
        )


@dataclass(frozen=True)
class RetreatProvidersAssembler:
    """Compose handler providers from configured modules."""

    modules: RetreatProviderModules

    def assemble(
        self,
        *,
        failures: Callable[[], RetreatFailureTranslator],
    ) -> RetreatHandlerProviders:
        workflow_factory = RetreatWorkflowProvidersFactory(module=self.modules.workflow)
        context_provider, failure_provider, workflow_provider = workflow_factory.create(
            failures=failures
        )
        orchestrator_factory = RetreatOrchestratorProvidersFactory(
            factory=self.modules.orchestrator,
            instrumentation=self.modules.instrumentation,
        )
        instrumentation_provider, orchestrator_provider = orchestrator_factory.create()
        outcome_factory = RetreatOutcomeProvidersFactory(module=self.modules.outcome)
        return RetreatHandlerProviders(
            context=context_provider,
            failures=failure_provider,
            workflow=workflow_provider,
            instrumentation=instrumentation_provider,
            orchestrator=orchestrator_provider,
            outcomes=outcome_factory.create(),
        )


def default_retreat_providers(
    *,
    failures: Callable[[], RetreatFailureTranslator],
    notes: Callable[[], RetreatFailureNotes],
    modules: RetreatProviderModules | None = None,
    module_factory: RetreatProviderModuleFactory | None = None,
) -> RetreatHandlerProviders:
    """Return providers wiring application services for retreat handling.

    The caller may provide a fully constructed module registry or a factory
    capable of creating one. When neither is supplied the default factory is
    used to compose modules with presentation defaults.
    """

    if modules is not None:
        registry = modules
    else:
        factory = module_factory or RetreatProviderModuleFactory(notes=notes)
        registry = factory.create()
    assembler = RetreatProvidersAssembler(modules=registry)
    return assembler.assemble(failures=failures)


__all__ = [
    "RetreatProviderModuleFactory",
    "RetreatProviderModules",
    "RetreatProvidersAssembler",
    "default_retreat_providers",
]

"""High level assembly helpers for retreat handler providers."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..protocols import RetreatFailureNotes, RetreatFailureTranslator
from .instrumentation import RetreatInstrumentationModule
from .orchestrator import (
    RetreatOrchestratorFactory,
    RetreatOrchestratorProvidersFactory,
    create_retreat_orchestrator_factory,
)
from .outcome import RetreatOutcomeModule, RetreatOutcomeProvidersFactory
from .workflow import RetreatWorkflowModule, RetreatWorkflowProvidersFactory


@dataclass(frozen=True)
class RetreatProviderModules:
    """Group modules used to compose retreat handler providers."""

    workflow: RetreatWorkflowModule
    orchestrator: RetreatOrchestratorFactory
    instrumentation: RetreatInstrumentationModule
    outcome: RetreatOutcomeModule

    @classmethod
    def default(
        cls,
        *,
        notes: Callable[[], RetreatFailureNotes],
        context_factory: Callable[[], "RetreatContextBuilder"] | None = None,
        orchestrator_factory: RetreatOrchestratorFactory | None = None,
        instrumentation: RetreatInstrumentationModule | None = None,
    ) -> "RetreatProviderModules":
        from ..context import RetreatContextBuilder

        context_builder = context_factory or RetreatContextBuilder
        return cls(
            workflow=RetreatWorkflowModule(context_builder),
            orchestrator=orchestrator_factory or create_retreat_orchestrator_factory(),
            instrumentation=instrumentation or RetreatInstrumentationModule(),
            outcome=RetreatOutcomeModule(notes),
        )


@dataclass(frozen=True)
class RetreatProvidersAssembler:
    """Compose handler providers from configured modules."""

    modules: RetreatProviderModules

    def assemble(
        self,
        *,
        failures: Callable[[], RetreatFailureTranslator],
    ) -> "RetreatHandlerProviders":
        from ..assembly import RetreatHandlerProviders

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
) -> "RetreatHandlerProviders":
    """Return providers wiring application services for retreat handling."""

    registry = modules or RetreatProviderModules.default(notes=notes)
    assembler = RetreatProvidersAssembler(modules=registry)
    return assembler.assemble(failures=failures)


__all__ = [
    "RetreatProviderModules",
    "RetreatProvidersAssembler",
    "default_retreat_providers",
]

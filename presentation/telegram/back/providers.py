"""Default providers bridging presentation layer with application services."""

from __future__ import annotations

from navigator.app.service.retreat_failure import RetreatFailureResolver
from .context import RetreatContextBuilder
from .factory import RetreatHandlerProviders
from .orchestrator import RetreatOrchestrator
from .outcome import RetreatOutcomeFactory
from .protocols import Translator
from .telemetry import RetreatTelemetry
from .workflow import RetreatWorkflow


def default_retreat_providers() -> RetreatHandlerProviders:
    """Return providers wiring application services for retreat handling."""

    def build_workflow(
        context: RetreatContextBuilder, failures: RetreatFailureResolver
    ) -> RetreatWorkflow:
        return RetreatWorkflow(context=context, failures=failures)

    def build_orchestrator(
        instrumentation: RetreatTelemetry, workflow: RetreatWorkflow
    ) -> RetreatOrchestrator:
        return RetreatOrchestrator(telemetry=instrumentation, workflow=workflow)

    def build_outcomes(translator: Translator) -> RetreatOutcomeFactory:
        return RetreatOutcomeFactory(translator)

    return RetreatHandlerProviders(
        context=RetreatContextBuilder,
        failures=RetreatFailureResolver,
        workflow=build_workflow,
        instrumentation=lambda telemetry: RetreatTelemetry(telemetry),
        orchestrator=build_orchestrator,
        outcomes=build_outcomes,
    )


__all__ = ["default_retreat_providers"]

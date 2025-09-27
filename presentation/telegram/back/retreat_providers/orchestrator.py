"""Orchestrator provider factories used by retreat handlers."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from navigator.core.telemetry import Telemetry

from ..failures import RetreatFailurePolicy
from ..orchestrator import RetreatOrchestrator
from ..reporting import RetreatOutcomeReporter
from ..runner import RetreatWorkflowRunner
from ..session import TelemetryScopeFactory
from ..telemetry import RetreatTelemetry
from ..workflow import RetreatWorkflow


@dataclass(frozen=True)
class RetreatOrchestratorFactory:
    """Create orchestrators while abstracting concrete implementations."""

    telemetry_factory: Callable[[RetreatTelemetry], TelemetryScopeFactory]
    failure_policy_factory: Callable[[], RetreatFailurePolicy]
    runner_factory: Callable[[RetreatWorkflow, RetreatFailurePolicy], RetreatWorkflowRunner]
    reporter_factory: Callable[[], RetreatOutcomeReporter]

    def create(
        self,
        instrumentation: RetreatTelemetry,
        workflow: RetreatWorkflow,
    ) -> RetreatOrchestrator:
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
class RetreatOrchestratorProvidersFactory:
    """Keep orchestration composition separate from workflow creation."""

    factory: RetreatOrchestratorFactory
    instrumentation: "RetreatInstrumentationModule"

    def create(
        self,
    ) -> tuple[
        Callable[[Telemetry], RetreatTelemetry],
        Callable[[RetreatTelemetry, RetreatWorkflow], RetreatOrchestrator],
    ]:
        return (self.instrumentation.build, self.factory.create)


def create_retreat_orchestrator_factory() -> RetreatOrchestratorFactory:
    """Construct a retreat orchestrator factory with default policies."""

    return RetreatOrchestratorFactory(
        telemetry_factory=TelemetryScopeFactory,
        failure_policy_factory=RetreatFailurePolicy,
        runner_factory=lambda workflow, policy: RetreatWorkflowRunner(workflow, policy),
        reporter_factory=RetreatOutcomeReporter,
    )


__all__ = [
    "RetreatOrchestratorFactory",
    "RetreatOrchestratorProvidersFactory",
    "create_retreat_orchestrator_factory",
]

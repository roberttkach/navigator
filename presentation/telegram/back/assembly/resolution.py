"""Resolution helpers for retreat handler collaborators."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.telemetry import Telemetry

from ..orchestrator import RetreatOrchestrator
from ..outcome import RetreatOutcomeFactory
from ..protocols import Translator
from ..telemetry import RetreatTelemetry

from .workflow import RetreatWorkflowBundle


@dataclass(slots=True)
class RetreatHandlerResolution:
    """Resolve orchestration and outcome collaborators for the handler."""

    telemetry: Telemetry
    translator: Translator
    providers: "RetreatHandlerProviders"
    overrides: "RetreatHandlerOverrides"

    def resolve_orchestrator(self, bundle: RetreatWorkflowBundle) -> RetreatOrchestrator:
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


if __debug__:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:  # pragma: no cover - imported lazily for typing only
        from .overrides import RetreatHandlerOverrides
        from .providers import RetreatHandlerProviders


__all__ = ["RetreatHandlerResolution"]

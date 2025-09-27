"""Provider descriptors for retreat handler collaborators."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Callable, TYPE_CHECKING

from navigator.core.telemetry import Telemetry

from ..orchestrator import RetreatOrchestrator
from ..outcome import RetreatOutcomeFactory
from ..protocols import RetreatFailureTranslator, Translator
from ..telemetry import RetreatTelemetry

if TYPE_CHECKING:  # pragma: no cover - type checking helpers
    from ..context import RetreatContextBuilder
    from ..workflow import RetreatWorkflow


@dataclass(frozen=True, slots=True)
class RetreatHandlerProviders:
    """Expose hooks to lazily create retreat handler collaborators."""

    context: Callable[[], "RetreatContextBuilder"]
    failures: Callable[[], RetreatFailureTranslator]
    workflow: Callable[["RetreatContextBuilder", RetreatFailureTranslator], "RetreatWorkflow"]
    instrumentation: Callable[[Telemetry], RetreatTelemetry]
    orchestrator: Callable[[RetreatTelemetry, "RetreatWorkflow"], RetreatOrchestrator]
    outcomes: Callable[[Translator], RetreatOutcomeFactory]


__all__ = ["RetreatHandlerProviders"]

"""Overrides specifying optional retreat handler collaborators."""
from __future__ import annotations

from dataclasses import dataclass

from ..orchestrator import RetreatOrchestrator
from ..outcome import RetreatOutcomeFactory
from ..protocols import RetreatFailureTranslator
from ..telemetry import RetreatTelemetry


@dataclass(frozen=True, slots=True)
class RetreatHandlerOverrides:
    """Optional dependencies that may replace individual collaborators."""

    context: "RetreatContextBuilder" | None = None
    failures: RetreatFailureTranslator | None = None
    workflow: "RetreatWorkflow" | None = None
    instrumentation: RetreatTelemetry | None = None
    orchestrator: RetreatOrchestrator | None = None
    outcomes: RetreatOutcomeFactory | None = None


if __debug__:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:  # pragma: no cover - imported lazily for typing only
        from ..context import RetreatContextBuilder
        from ..workflow import RetreatWorkflow


__all__ = ["RetreatHandlerOverrides"]

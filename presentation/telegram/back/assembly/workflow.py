"""Workflow bundle resolved during retreat handler assembly."""
from __future__ import annotations

from dataclasses import dataclass

from ..protocols import RetreatFailureTranslator


@dataclass(frozen=True, slots=True)
class RetreatWorkflowBundle:
    """Capture the workflow-related collaborators for handler assembly."""

    context: "RetreatContextBuilder"
    failures: RetreatFailureTranslator
    workflow: "RetreatWorkflow"

    @classmethod
    def from_overrides(
        cls,
        overrides: "RetreatHandlerOverrides",
        providers: "RetreatHandlerProviders",
    ) -> "RetreatWorkflowBundle":
        """Resolve workflow collaborators using overrides when present."""

        context = overrides.context or providers.context()
        failures = overrides.failures or providers.failures()
        workflow = overrides.workflow or providers.workflow(context, failures)
        return cls(context=context, failures=failures, workflow=workflow)


if __debug__:
    from typing import TYPE_CHECKING

    if TYPE_CHECKING:  # pragma: no cover - imported lazily for typing only
        from ..context import RetreatContextBuilder
        from ..workflow import RetreatWorkflow
        from .overrides import RetreatHandlerOverrides
        from .providers import RetreatHandlerProviders


__all__ = ["RetreatWorkflowBundle"]

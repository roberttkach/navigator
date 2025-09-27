"""Workflow related provider factories for retreat handlers."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..context import RetreatContextBuilder
from ..protocols import RetreatFailureTranslator
from ..workflow import RetreatWorkflow


@dataclass(frozen=True)
class RetreatWorkflowModule:
    """Provide factories building workflow-related collaborators."""

    context_factory: Callable[[], RetreatContextBuilder]

    def context(self) -> RetreatContextBuilder:
        return self.context_factory()

    def workflow(
        self,
        context: RetreatContextBuilder,
        failures: RetreatFailureTranslator,
    ) -> RetreatWorkflow:
        return RetreatWorkflow.from_builders(context=context, failures=failures)


@dataclass(frozen=True)
class RetreatWorkflowProvidersFactory:
    """Compose workflow related providers without touching orchestrators."""

    module: RetreatWorkflowModule

    def create(
        self,
        *,
        failures: Callable[[], RetreatFailureTranslator],
    ) -> tuple[
        Callable[[], RetreatContextBuilder],
        Callable[[], RetreatFailureTranslator],
        Callable[[RetreatContextBuilder, RetreatFailureTranslator], RetreatWorkflow],
    ]:
        return (self.module.context, failures, self.module.workflow)


__all__ = [
    "RetreatWorkflowModule",
    "RetreatWorkflowProvidersFactory",
]

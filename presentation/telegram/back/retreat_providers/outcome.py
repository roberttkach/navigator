"""Outcome related provider factories used in retreat handlers."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass

from ..outcome import RetreatOutcomeFactory
from ..protocols import RetreatFailureNotes, Translator


@dataclass(frozen=True)
class RetreatOutcomeModule:
    """Create factories translating retreat outcomes."""

    notes_factory: Callable[[], RetreatFailureNotes]

    def build(self, translator: Translator) -> RetreatOutcomeFactory:
        return RetreatOutcomeFactory(translator, self.notes_factory())


@dataclass(frozen=True)
class RetreatOutcomeProvidersFactory:
    """Expose only the outcome providers assembly responsibilities."""

    module: RetreatOutcomeModule

    def create(self) -> Callable[[Translator], RetreatOutcomeFactory]:
        return self.module.build


__all__ = [
    "RetreatOutcomeModule",
    "RetreatOutcomeProvidersFactory",
]

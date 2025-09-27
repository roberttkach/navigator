"""Definitions describing dependencies required to build retreat handlers."""
from __future__ import annotations

from collections.abc import Callable
from dataclasses import dataclass, field

from navigator.core.telemetry import Telemetry
from navigator.presentation.alerts import lexeme
from navigator.presentation.telegram.failures import (
    default_retreat_failure_notes,
    default_retreat_failure_translator,
)

from .protocols import RetreatFailureNotes, RetreatFailureTranslator, Translator


@dataclass(frozen=True)
class RetreatDependencyOverrides:
    """Factory hooks that allow customizing handler dependencies."""

    failures: Callable[[], RetreatFailureTranslator]
    notes: Callable[[], RetreatFailureNotes]


@dataclass(frozen=True)
class RetreatDependencies:
    """Dependencies required to configure retreat handling."""

    telemetry: Telemetry
    translator: Translator = lexeme
    failures: Callable[[], RetreatFailureTranslator] = field(
        default=default_retreat_failure_translator,
    )
    notes: Callable[[], RetreatFailureNotes] = field(
        default=default_retreat_failure_notes,
    )

    def overrides(self) -> RetreatDependencyOverrides:
        """Return strongly typed override factories for handler configuration."""

        return RetreatDependencyOverrides(failures=self.failures, notes=self.notes)


__all__ = ["RetreatDependencies", "RetreatDependencyOverrides"]

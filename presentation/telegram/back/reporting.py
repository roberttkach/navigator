"""Outcome reporting utilities for retreat orchestration."""
from __future__ import annotations

from .result import RetreatResult
from .session import TelemetryScopeSession


class RetreatOutcomeReporter:
    """Report workflow outcomes through telemetry sessions."""

    def __init__(self, default_note: str = "generic") -> None:
        self._default_note = default_note

    def report(self, result: RetreatResult, session: TelemetryScopeSession) -> RetreatResult:
        """Emit telemetry around the supplied result and return it unchanged."""

        if result.success:
            session.complete()
        else:
            session.fail(result.note or self._default_note)
        return result


__all__ = ["RetreatOutcomeReporter"]

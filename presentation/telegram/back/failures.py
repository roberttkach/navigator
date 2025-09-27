"""Failure handling policies for retreat workflows.""" 
from __future__ import annotations

from .result import RetreatResult


class RetreatFailurePolicy:
    """Translate unexpected workflow errors into retreat outcomes."""

    def __init__(self, default_note: str = "generic") -> None:
        self._default_note = default_note

    def handle(self, error: Exception) -> RetreatResult:
        """Convert an exception into a failed retreat result."""

        del error  # defensive branch - logging handled upstream
        return RetreatResult.failed(self._default_note)


__all__ = ["RetreatFailurePolicy"]

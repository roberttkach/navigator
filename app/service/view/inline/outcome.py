"""Shared inline outcome model used across flow components."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.service.rendering import decision as D

from ..executor import Execution
from typing import TYPE_CHECKING


@dataclass(slots=True)
class InlineOutcome:
    """Capture the result of inline reconciliation."""

    execution: Execution
    decision: D.Decision
    payload: "Payload"


if TYPE_CHECKING:
    from navigator.core.value.content import Payload


__all__ = ["InlineOutcome"]

"""Shared runtime builder context objects."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.app.locks.guard import Guardian
from navigator.core.value.message import Scope


@dataclass(frozen=True)
class RuntimeBuildContext:
    """Shared context values reused across specialised runtime builders."""

    guard: Guardian
    scope: Scope


__all__ = ["RuntimeBuildContext"]

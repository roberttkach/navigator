"""Shared type aliases used across navigator runtime components."""
from __future__ import annotations

from typing import Callable

from navigator.core.value.message import Scope


MissingAlert = Callable[[Scope], str]

__all__ = ["MissingAlert"]

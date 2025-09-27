"""Shared type aliases used across navigator runtime components."""
from __future__ import annotations

from typing import Callable

from navigator.core.value.message import Scope
from navigator.core.contracts.state import StateLike


MissingAlert = Callable[[Scope], str]


__all__ = ["MissingAlert", "StateLike"]

"""Shared type aliases used across navigator runtime components."""
from __future__ import annotations

from typing import Callable, Protocol

from navigator.core.value.message import Scope


MissingAlert = Callable[[Scope], str]


class StateLike(Protocol):
    """Protocol describing objects exposing an FSM state string."""

    state: str


__all__ = ["MissingAlert", "StateLike"]

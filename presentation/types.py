from __future__ import annotations

from typing import Protocol


class StateLike(Protocol):
    """Protocol describing objects exposing an FSM state string."""

    state: str


__all__ = ["StateLike"]

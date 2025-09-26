"""Protocols describing renderer outcomes expected by use cases."""

from __future__ import annotations

from typing import Protocol, Sequence, runtime_checkable

from navigator.core.typing.result import Meta


@runtime_checkable
class RenderOutcome(Protocol):
    """Structural contract produced by view planners."""

    ids: Sequence[int]
    extras: Sequence[Sequence[int]]
    metas: Sequence[Meta]
    changed: bool


__all__ = ["RenderOutcome"]


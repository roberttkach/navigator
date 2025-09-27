"""Protocols describing renderer outcomes expected by use cases."""

from __future__ import annotations

from typing import Optional, Protocol, Sequence, runtime_checkable

from navigator.core.entity.history import Entry
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope
from navigator.core.typing.result import Meta


@runtime_checkable
class RenderOutcome(Protocol):
    """Structural contract produced by view planners."""

    ids: Sequence[int]
    extras: Sequence[Sequence[int]]
    metas: Sequence[Meta]
    changed: bool


@runtime_checkable
class RenderPlanner(Protocol):
    """Structural contract for components able to plan renders."""

    async def render(
        self,
        scope: Scope,
        payloads: Sequence[Payload],
        trail: Entry | None,
        *,
        inline: bool,
    ) -> Optional[RenderOutcome]:
        ...


__all__ = ["RenderOutcome", "RenderPlanner"]


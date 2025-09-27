"""Factories building tail views from scoped identifiers."""
from __future__ import annotations

from dataclasses import dataclass

from navigator.core.value.message import Scope

from ..tail_view import TailView


@dataclass(frozen=True)
class TailViewFactory:
    """Create :class:`TailView` instances for navigator tail operations."""

    def create(self, *, scope: Scope, identifier: int) -> TailView:
        """Build a tail view preserving scope-specific flags."""

        return TailView(
            identifier=identifier,
            inline=bool(scope.inline),
            chat=scope.chat,
        )


__all__ = ["TailViewFactory"]

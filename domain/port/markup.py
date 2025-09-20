from __future__ import annotations

from typing import Protocol, Optional, Any, runtime_checkable

from ..entity.markup import Markup


@runtime_checkable
class MarkupCodec(Protocol):
    """Codec to serialize and deserialize reply markups."""

    def encode(self, markup: Any) -> Optional[Markup]:
        """Convert native markup to storable Markup."""

    def decode(self, stored: Optional[Markup]) -> Any:
        """Convert stored Markup to native markup."""


__all__ = ["MarkupCodec"]

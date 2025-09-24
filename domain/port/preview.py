from __future__ import annotations

from typing import Any, Optional, Protocol, runtime_checkable

from ..value.content import Preview


@runtime_checkable
class LinkPreviewCodec(Protocol):
    """Codec for platform-specific link preview representations."""

    def encode(self, preview: Preview) -> Any:
        """Convert domain Preview to a native representation."""

    def decode(self, data: Any) -> Optional[Preview]:
        """Parse a native representation into a domain Preview."""


__all__ = ["LinkPreviewCodec"]

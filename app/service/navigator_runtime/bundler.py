"""Payload bundling utilities used by navigator history operations."""
from __future__ import annotations

from navigator.app.dto.content import Content, Node
from navigator.app.map.payload import collect
from navigator.core.value.content import Payload


class PayloadBundler:
    """Transform DTO content into payload bundles."""

    def bundle(self, content: Content | Node) -> list[Payload]:
        node = content if isinstance(content, Node) else Node(messages=[content])
        return collect(node)


__all__ = ["PayloadBundler"]

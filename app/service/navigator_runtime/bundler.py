"""Payload bundling utilities used by navigator history operations."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol, Sequence

from navigator.app.dto.content import Content, Node
from navigator.app.map.payload import collect
from navigator.core.value.content import Payload


class PayloadBundleSource(Protocol):
    """Describe inputs that can be materialised into payload bundles."""

    def materialize(self, bundler: "PayloadBundler") -> list[Payload]:
        """Return payloads using the provided ``bundler`` implementation."""


@dataclass(frozen=True)
class _NodeBundleSource:
    """Bundle source wrapping DTO ``Node`` instances."""

    node: Node

    def materialize(self, bundler: "PayloadBundler") -> list[Payload]:
        return collect(self.node)


@dataclass(frozen=True)
class _ContentBundleSource:
    """Bundle source wrapping single DTO ``Content`` messages."""

    content: Content

    def materialize(self, bundler: "PayloadBundler") -> list[Payload]:
        return collect(Node(messages=[self.content]))


@dataclass(frozen=True)
class _PayloadSequenceSource:
    """Bundle source for pre-built payload collections."""

    payloads: Sequence[Payload]

    def materialize(self, bundler: "PayloadBundler") -> list[Payload]:
        return list(self.payloads)


class PayloadBundler:
    """Transform heterogeneous content sources into payload bundles."""

    def bundle(self, source: PayloadBundleSource) -> list[Payload]:
        return source.materialize(self)


def bundle_from_dto(candidate: Content | Node) -> PayloadBundleSource:
    """Return a bundle source wrapping DTO content primitives."""

    if isinstance(candidate, Node):
        return _NodeBundleSource(candidate)
    return _ContentBundleSource(candidate)


def bundle_from_payloads(payloads: Sequence[Payload]) -> PayloadBundleSource:
    """Wrap existing payload sequences into bundle sources."""

    return _PayloadSequenceSource(payloads)


__all__ = [
    "PayloadBundleSource",
    "PayloadBundler",
    "bundle_from_dto",
    "bundle_from_payloads",
]

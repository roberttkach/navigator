"""DTO adapters describing navigator tail edit requests."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

from navigator.app.dto.content import Content
from navigator.core.value.content import Payload

from .converter import TailPayloadConverter


@dataclass(frozen=True)
class TailEditDescription:
    """Describe structural properties of a tail edit request."""

    text: bool
    media: bool
    group: bool


class TailEditRequest(Protocol):
    """Represent edit requests accepted by tail gateways."""

    def describe(self) -> TailEditDescription:
        """Return boolean feature flags describing the payload."""

    def payload(self, converter: TailPayloadConverter) -> Payload:
        """Return payload representation for downstream use cases."""


@dataclass(frozen=True)
class TailContentEditRequest:
    """Adapter wrapping DTO ``Content`` for tail edits."""

    content: Content

    def describe(self) -> TailEditDescription:
        return TailEditDescription(
            text=bool(self.content.text),
            media=bool(self.content.media),
            group=bool(self.content.group),
        )

    def payload(self, converter: TailPayloadConverter) -> Payload:
        return converter.convert(self.content)


@dataclass(frozen=True)
class TailPayloadEditRequest:
    """Adapter wrapping pre-built payloads for tail edits."""

    entry: Payload

    def describe(self) -> TailEditDescription:
        return TailEditDescription(
            text=bool(self.entry.text),
            media=bool(self.entry.media),
            group=bool(self.entry.group),
        )

    def payload(self, converter: TailPayloadConverter) -> Payload:
        return self.entry


def dto_edit_request(content: Content) -> TailEditRequest:
    """Create a tail edit request from ``Content`` DTO objects."""

    return TailContentEditRequest(content)


def payload_edit_request(entry: Payload) -> TailEditRequest:
    """Create a tail edit request from an existing payload."""

    return TailPayloadEditRequest(entry)


__all__ = [
    "TailContentEditRequest",
    "TailEditDescription",
    "TailEditRequest",
    "TailPayloadEditRequest",
    "dto_edit_request",
    "payload_edit_request",
]

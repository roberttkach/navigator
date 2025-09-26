"""Payload conversion helpers used by tail edit requests."""
from __future__ import annotations

from navigator.app.dto.content import Content
from navigator.app.map.payload import convert
from navigator.core.value.content import Payload


class TailPayloadConverter:
    """Translate tail DTOs into payloads accepted by the use case flow."""

    def convert(self, content: Content) -> Payload:
        return convert(content)


__all__ = ["TailPayloadConverter"]

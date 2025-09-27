"""Helpers sanitising entry extras for persisted messages."""
from __future__ import annotations

from typing import Any, Optional

from ...core.entity.history import Entry
from ...core.service.history.extra import cleanse
from ...core.util.entities import EntitySanitizer
from ...core.value.content import Payload


class ExtraSanitizer:
    """Sanitise message extras using payload data and previous history."""

    def __init__(self, *, entities: EntitySanitizer) -> None:
        self._entities = entities

    def sanitize(
        self,
        payload: Payload,
        *,
        base: Optional[Entry],
        index: int,
        length: int,
    ) -> Optional[dict[str, Any]]:
        source = payload.extra if payload.extra is not None else self._previous_extra(base, index)
        return cleanse(source, length=length, entities=self._entities)

    @staticmethod
    def _previous_extra(base: Optional[Entry], index: int) -> Optional[dict[str, Any]]:
        if base is None:
            return None
        messages = getattr(base, "messages", None) or []
        if index >= len(messages):
            return None
        return messages[index].extra


__all__ = ["ExtraSanitizer"]

"""Shared data models for edit execution."""

from __future__ import annotations

from dataclasses import dataclass

from navigator.core.entity.history import Entry, Message
from navigator.core.port.message import Result
from typing import Optional


def head(entity: Entry | Message | None) -> Optional[Message]:
    """Return the most recent message associated with ``entity``."""

    if entity is None:
        return None
    if isinstance(entity, Message):
        return entity
    if getattr(entity, "messages", None):
        try:
            return entity.messages[0]
        except Exception:  # pragma: no cover - defensive
            return None
    return None


@dataclass(slots=True)
class Execution:
    """Capture the gateway response alongside the stem message."""

    result: Result
    stem: Message | None


__all__ = ["Execution", "head"]


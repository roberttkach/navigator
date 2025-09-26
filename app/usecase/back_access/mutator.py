"""History mutation helpers for rewind flows."""
from __future__ import annotations

from dataclasses import replace

from navigator.core.entity.history import Entry


class RewindMutator:
    """Mutate entries using render metadata."""

    def rebuild(self, target: Entry, render: object) -> Entry:
        identifiers = self.identifiers(render)
        extras = self.extras(render)
        limit = min(len(target.messages), len(identifiers))
        messages = list(target.messages)

        for index in range(limit):
            message = target.messages[index]
            provided = (
                extras[index]
                if index < len(extras)
                else list(message.extras or [])
            )
            messages[index] = replace(
                message,
                id=int(identifiers[index]),
                extras=list(provided),
            )

        return replace(target, messages=messages)

    def identifiers(self, render: object) -> list[int]:
        raw = getattr(render, "ids", None) or []
        return [int(identifier) for identifier in raw]

    def extras(self, render: object) -> list[list[int]]:
        raw = getattr(render, "extras", None) or []
        return [list(extra) for extra in raw]

    def primary_identifier(self, render: object) -> int | None:
        identifiers = self.identifiers(render)
        return identifiers[0] if identifiers else None

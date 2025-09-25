"""Provide mutation helpers for tail history operations."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import replace

from navigator.core.entity.history import Entry, Message


class TailHistoryMutator:
    """Encapsulate history mutation helpers used by tail use-cases."""

    def reindex(
            self,
            entry: Entry,
            identifiers: Sequence[int],
            extras: Sequence[Sequence[int]] | None = None,
    ) -> Entry:
        """Rebuild entry messages with provided identifiers and extras."""

        limit = min(len(entry.messages), len(identifiers))
        if limit == 0:
            return entry

        updated: list[Message] = []
        for index in range(limit):
            message = entry.messages[index]
            provided = (
                list(extras[index])
                if extras is not None and index < len(extras)
                else message.extras
            )
            updated.append(
                replace(
                    message,
                    id=int(identifiers[index]),
                    extras=provided,
                )
            )

        if limit < len(entry.messages):
            updated.extend(entry.messages[limit:])

        return replace(entry, messages=updated)


__all__ = ["TailHistoryMutator"]

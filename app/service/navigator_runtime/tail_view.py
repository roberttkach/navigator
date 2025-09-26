"""Domain views describing navigator tail metadata."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class TailView:
    """Immutable representation of the last navigator message."""

    identifier: int
    inline: bool
    chat: int | None

    def to_mapping(self) -> dict[str, object]:
        """Return a serialisable mapping compatible with legacy consumers."""

        return {"id": self.identifier, "inline": self.inline, "chat": self.chat}


__all__ = ["TailView"]


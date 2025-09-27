"""Outcome wrapper exposing rendering metadata accessors."""
from __future__ import annotations

from typing import List, Optional, Sequence

from ...core.error import MetadataKindMissing
from ...core.typing.result import Meta


class Outcome:
    """Provide convenient accessors around rendering outcome metadata."""

    def __init__(
        self,
        ids: Sequence[int],
        extras: Optional[Sequence[Sequence[int]]],
        metas: Sequence[Meta],
    ) -> None:
        self.ids = [int(identifier) for identifier in ids]
        self.extras = [list(extra) for extra in extras or []]
        self.metas = list(metas or [])

    def id_at(self, index: int) -> int:
        return self.ids[index]

    def extras_at(self, index: int) -> List[int]:
        if index < len(self.extras):
            return list(self.extras[index])
        return []

    def meta_at(self, index: int) -> Meta:
        if index >= len(self.metas):
            raise MetadataKindMissing()
        return self.metas[index]


__all__ = ["Outcome"]

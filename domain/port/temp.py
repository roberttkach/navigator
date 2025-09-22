from __future__ import annotations

import typing
from typing import Protocol, List


@typing.runtime_checkable
class TemporaryRepository(Protocol):
    """Storage for temporary message ids."""

    async def collect(self) -> List[int]:
        """Return list of ids."""

    async def stash(self, ids: List[int]) -> None:
        """Persist list of ids."""


__all__ = ["TemporaryRepository"]

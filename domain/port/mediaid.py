from __future__ import annotations

from typing import Protocol, runtime_checkable


@runtime_checkable
class MediaIdentityPolicy(Protocol):
    """Policy to compare media identity across history and payloads."""

    def same(self, former: object, latter: object, *, type: str) -> bool:
        """Return True if the media instances refer to the same underlying object."""


__all__ = ["MediaIdentityPolicy"]

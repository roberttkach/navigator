from __future__ import annotations

from navigator.core.entity.media import MediaType
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.value.content import Payload


class InlineGuard:
    """Check whether a payload can be edited within inline constraints."""

    def __init__(self, policy: MediaPathPolicy) -> None:
        self._policy = policy

    def admissible(self, payload: Payload) -> bool:
        media = _first(payload)
        if media is None:
            return False
        if media.type in (MediaType.VOICE, MediaType.VIDEO_NOTE):
            return False
        return self._policy.admissible(media.path, inline=True)


def _first(payload: Payload):
    if getattr(payload, "media", None):
        return payload.media
    group = getattr(payload, "group", None)
    if group:
        return group[0]
    return None


__all__ = ["InlineGuard"]

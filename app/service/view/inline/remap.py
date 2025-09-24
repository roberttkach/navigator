from __future__ import annotations

from navigator.core.entity.history import Message
from navigator.core.service.rendering import decision as D
from navigator.core.value.content import Payload


class InlineRemapper:
    """Translate DELETE_SEND decisions for inline scenarios."""

    def remap(self, base: Message | None, fresh: Payload) -> D.Decision:
        origin_media = bool(getattr(base, "media", None) or getattr(base, "group", None))
        fresh_media = bool(getattr(fresh, "media", None) or getattr(fresh, "group", None))
        if origin_media and not fresh_media:
            return D.Decision.EDIT_MARKUP
        if not origin_media and fresh_media:
            return D.Decision.DELETE_SEND
        return D.Decision.EDIT_MEDIA if origin_media else D.Decision.EDIT_TEXT


__all__ = ["InlineRemapper"]

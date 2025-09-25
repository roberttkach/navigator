from __future__ import annotations

from navigator.core.entity.history import Message
from navigator.core.service.rendering import decision as D
from navigator.core.value.content import Payload


class InlineRemapper:
    """Translate DELETE_SEND decisions for inline scenarios."""

    def remap(self, base: Message | None, fresh: Payload) -> D.Decision:
        originrich = bool(getattr(base, "media", None) or getattr(base, "group", None))
        freshrich = bool(getattr(fresh, "media", None) or getattr(fresh, "group", None))
        if originrich and not freshrich:
            return D.Decision.EDIT_MARKUP
        if not originrich and freshrich:
            return D.Decision.DELETE_SEND
        return D.Decision.EDIT_MEDIA if originrich else D.Decision.EDIT_TEXT


__all__ = ["InlineRemapper"]

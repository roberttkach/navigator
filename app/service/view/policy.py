from __future__ import annotations

from typing import Optional

from ....core.entity.markup import Markup
from ....core.value.content import Payload
from ....core.value.message import Scope

_INLINE_KEYBOARD_KIND = "InlineKeyboardMarkup"


def permit(scope: Scope, reply: Optional[Markup]) -> Optional[Markup]:
    """Return reply markup allowed for the given scope.

    Scope-specific restrictions limit business chats and non-private/group chats to
    inline keyboards only. Private and group chats may use any supported markup.
    """
    if reply is None:
        return None

    if bool(getattr(scope, "business", None)):
        return reply if reply.kind == _INLINE_KEYBOARD_KIND else None

    category = getattr(scope, "category", None)
    if category in {"private", "group"}:
        return reply

    return reply if reply.kind == _INLINE_KEYBOARD_KIND else None


def adapt(scope: Scope, payload: Payload) -> Payload:
    allowed = permit(scope, payload.reply)
    if allowed is payload.reply:
        return payload
    return payload.morph(reply=allowed)


__all__ = ["permit", "adapt"]

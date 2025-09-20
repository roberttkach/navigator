from __future__ import annotations

from typing import Optional

from ....domain.entity.markup import Markup
from ....domain.value.content import Payload
from ....domain.value.message import Scope

_INLINE_KEYBOARD_KIND = "InlineKeyboardMarkup"


def allowed_reply(scope: Scope, reply: Optional[Markup]) -> Optional[Markup]:
    """Return reply markup allowed for the given scope.

    Scope-specific restrictions limit business chats and non-private/group chats to
    inline keyboards only. Private and group chats may use any supported markup.
    """
    if reply is None:
        return None

    if bool(getattr(scope, "business", None)):
        return reply if reply.kind == _INLINE_KEYBOARD_KIND else None

    chat_kind = getattr(scope, "category", None)
    if chat_kind in {"private", "group"}:
        return reply

    return reply if reply.kind == _INLINE_KEYBOARD_KIND else None


def payload_with_allowed_reply(scope: Scope, payload: Payload) -> Payload:
    allowed = allowed_reply(scope, payload.reply)
    if allowed is payload.reply:
        return payload
    return payload.morph(reply=allowed)


__all__ = ["allowed_reply", "payload_with_allowed_reply"]

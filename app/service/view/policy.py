"""Define reply markup policy adjustments per scope."""

from __future__ import annotations

from typing import Optional

from ....core.entity.markup import Markup
from ....core.value.content import Payload
from ....core.value.message import Scope

_INLINE_KEYBOARD_KIND = "InlineKeyboardMarkup"


def _inline_only(scope: Scope) -> bool:
    """Report whether ``scope`` may only use inline keyboard markup."""

    if bool(getattr(scope, "business", None)):
        return True
    category = getattr(scope, "category", None)
    return category not in {"private", "group"}


def permit(scope: Scope, reply: Optional[Markup]) -> Optional[Markup]:
    """Return reply markup allowed for the given scope."""

    if reply is None:
        return None
    if _inline_only(scope) and reply.kind != _INLINE_KEYBOARD_KIND:
        return None
    return reply


def adapt(scope: Scope, payload: Payload) -> Payload:
    allowed = permit(scope, payload.reply)
    if allowed is payload.reply:
        return payload
    return payload.morph(reply=allowed)


__all__ = ["permit", "adapt"]

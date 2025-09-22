from __future__ import annotations

from ....domain.service.rendering import decision as D
from ....domain.value.content import Payload


def remap(origin, fresh: Payload, *, inline: bool) -> D.Decision:
    """
    Единый ремап для inline при изначальном DELETE_SEND.

    Правила:
    - Inline запрещает media↔text. Разрешить только EDIT_MARKUP при медиа→текст.
    - Если оба текст — EDIT_TEXT.
    - Если оба медиа — EDIT_MEDIA.
    - Иначе оставить DELETE_SEND.
    """
    if not inline:
        return D.Decision.DELETE_SEND

    origin = bool(getattr(origin, "media", None) or getattr(origin, "group", None))
    fresh = bool(getattr(fresh, "media", None) or getattr(fresh, "group", None))

    if origin and not fresh:
        return D.Decision.EDIT_MARKUP
    if (not origin) and fresh:
        return D.Decision.DELETE_SEND
    return D.Decision.EDIT_MEDIA if origin else D.Decision.EDIT_TEXT

from __future__ import annotations

from ....domain.service.rendering import decision as D
from ....domain.value.content import Payload


def remap(old_msg, new: Payload, *, inline: bool) -> D.Decision:
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

    o_has_media = bool(getattr(old_msg, "media", None) or getattr(old_msg, "group", None))
    n_has_media = bool(getattr(new, "media", None) or getattr(new, "group", None))

    if o_has_media and not n_has_media:
        return D.Decision.EDIT_MARKUP
    if (not o_has_media) and n_has_media:
        return D.Decision.DELETE_SEND
    return D.Decision.EDIT_MEDIA if o_has_media else D.Decision.EDIT_TEXT

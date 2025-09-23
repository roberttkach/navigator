from datetime import datetime, timezone

from ...domain.entity.history import Entry, Message
from ...domain.entity.media import MediaItem
from ...domain.service.history.extra import cleanse
from ...domain.value.content import Payload, caption

SHIELD_MESSAGE = "Inline message does not support media groups"


def prime(id: int, payload: Payload) -> Entry:
    media = None
    if payload.media:
        media = MediaItem(type=payload.media.type, path=payload.media.path, caption=caption(payload))

    if payload.group:
        first = payload.group[0] if payload.group else None
        length = len((getattr(first, "caption", None) or ""))
    elif payload.media:
        length = len((caption(payload) or ""))
    elif isinstance(payload.text, str):
        length = len(payload.text)
    else:
        length = 0

    extra = cleanse(payload.extra, length=length)
    message = Message(
        id=id,
        text=None if (payload.media or payload.group) else payload.text,
        media=media,
        group=payload.group,
        markup=None,
        preview=payload.preview,
        extra=extra,
        automated=True,
        ts=datetime.now(timezone.utc),
    )
    return Entry(
        state=None,
        view=None,
        messages=[message],
    )


def shield(scope, payload):
    if getattr(scope, "inline", None) and getattr(payload, "group", None):
        from ...domain.error import InlineUnsupported
        raise InlineUnsupported(SHIELD_MESSAGE)


TailPrune: bool = True

InlineTailDelete: bool = False

ResendOnBan: bool = True

ResendOnIdle: bool = False

ImplicitCaption: bool = True

StrictAbort: bool = False

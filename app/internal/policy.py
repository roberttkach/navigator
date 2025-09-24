from datetime import datetime, timezone
from typing import Iterable

from ...core.entity.history import Entry, Message
from ...core.entity.media import MediaItem
from ...core.service.history.extra import cleanse
from ...core.value.content import Payload, caption

SHIELD_MESSAGE = "Inline message does not support media groups"
SHIELD_NODE_MESSAGE = "Inline message does not support multi-message nodes"


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


def _materialize(payloads: Payload | Iterable[Payload] | None) -> list[Payload]:
    if payloads is None:
        return []
    if isinstance(payloads, Payload):
        return [payloads]
    if isinstance(payloads, Iterable):
        return [item for item in payloads if item is not None]
    raise TypeError("payloads must be Payload or iterable of Payload")


def validate_inline(
        scope,
        payloads: Payload | Iterable[Payload] | None,
        *,
        inline: bool | None = None,
) -> None:
    active = inline if inline is not None else bool(getattr(scope, "inline", None))
    if not active:
        return

    samples = _materialize(payloads)
    if len(samples) > 1:
        from ...core.error import InlineUnsupported
        raise InlineUnsupported(SHIELD_NODE_MESSAGE)

    for sample in samples:
        if getattr(sample, "group", None):
            from ...core.error import InlineUnsupported
            raise InlineUnsupported(SHIELD_MESSAGE)


def shield(scope, payload):
    validate_inline(scope, payload)

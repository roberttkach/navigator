"""Helpers for constructing history entries from payload snapshots."""

from __future__ import annotations

from datetime import datetime, timezone

from navigator.core.entity.history import Entry, Message
from navigator.core.entity.media import MediaItem
from navigator.core.service.history.extra import cleanse
from navigator.core.value.content import Payload, caption


def prime(identifier: int, payload: Payload) -> Entry:
    media = None
    if payload.media:
        media = MediaItem(
            type=payload.media.type,
            path=payload.media.path,
            caption=caption(payload),
        )

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
        id=identifier,
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


__all__ = ["prime"]

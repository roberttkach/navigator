from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Dict

from ..entity.markup import Markup
from ..entity.media import MediaItem

if TYPE_CHECKING:
    from ..entity.history import Entry


@dataclass(frozen=True, slots=True)
class Preview:
    url: str | None = None
    small: bool = False
    large: bool = False
    above: bool = False
    disabled: bool | None = None


@dataclass(frozen=True, slots=True)
class Payload:
    text: str | None = None
    media: MediaItem | None = None
    group: list[MediaItem] | None = None
    reply: Markup | None = None
    preview: Preview | None = None
    extra: Dict[str, Any] | None = None
    erase: bool = False

    def morph(self, **kw: Any) -> Payload:
        return replace(self, **kw)


def normalize(payload: Payload) -> Payload:
    media = payload.media
    group = payload.group
    if group and len(group) == 1:
        media = group[0]
        group = None
    if media and group:
        raise ValueError("payload_has_both_media_and_group")
    text = None if group else payload.text
    return Payload(
        text=text,
        media=media,
        group=group,
        reply=payload.reply,
        preview=payload.preview,
        extra=payload.extra,
        erase=payload.erase and not bool(group),
    )


def caption(x: Payload | Entry | None) -> str | None:
    """Return prioritized caption text for media payloads."""
    if x is None:
        return None
    if getattr(x, "group", None):
        return None
    m = getattr(x, "media", None)
    if not m:
        return None
    t = getattr(x, "text", None)
    if isinstance(t, str):
        s = t.strip()
        if s:
            return s
    c = getattr(m, "caption", None)
    if isinstance(c, str):
        s = str(c).strip()
        return s if s else None
    return None

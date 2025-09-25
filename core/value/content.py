"""Define content payload structures and utilities."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Any, Dict, Iterable

from ..entity.markup import Markup
from ..entity.media import MediaItem

if TYPE_CHECKING:
    from ..entity.history import Entry


@dataclass(frozen=True, slots=True)
class Preview:
    """Encapsulate preview display hints for outbound messages."""

    url: str | None = None
    small: bool = False
    large: bool = False
    above: bool = False
    disabled: bool | None = None


@dataclass(frozen=True, slots=True)
class Payload:
    """Bundle outbound message artefacts for transport layers."""

    text: str | None = None
    media: MediaItem | None = None
    group: list[MediaItem] | None = None
    reply: Markup | None = None
    preview: Preview | None = None
    extra: Dict[str, Any] | None = None
    erase: bool = False

    def morph(self, **kw: Any) -> Payload:
        """Return a copy of the payload updated with ``kw`` overrides."""

        return replace(self, **kw)


def normalize(payload: Payload) -> Payload:
    """Return a payload with mutually exclusive media and group."""

    media, group = _disambiguate_media(payload.media, payload.group)
    return Payload(
        text=_text_for_group(payload.text, group),
        media=media,
        group=group,
        reply=payload.reply,
        preview=payload.preview,
        extra=payload.extra,
        erase=payload.erase and not bool(group),
    )


def caption(candidate: Payload | Entry | None) -> str | None:
    """Return prioritised caption text for media payloads."""

    if candidate is None or getattr(candidate, "group", None):
        return None

    media = getattr(candidate, "media", None)
    if media is None:
        return None

    text = getattr(candidate, "text", None)
    usable = _first_non_empty((text, getattr(media, "caption", None)))
    return usable.strip() if isinstance(usable, str) else None


def _disambiguate_media(
        media: MediaItem | None,
        group: Iterable[MediaItem] | None,
) -> tuple[MediaItem | None, list[MediaItem] | None]:
    """Return harmonised media and group members from user input."""

    items = list(group) if group else []
    if media and items:
        raise ValueError("payload_has_both_media_and_group")
    if len(items) == 1 and media is None:
        return items[0], None
    return media, items or None


def _text_for_group(text: str | None, group: list[MediaItem] | None) -> str | None:
    """Drop text when grouped media is present per platform rules."""

    return None if group else text


def _first_non_empty(values: Iterable[object]) -> str | None:
    """Return the first non-empty string-like value from ``values``."""

    for value in values:
        if isinstance(value, str) and value.strip():
            return value
    return None

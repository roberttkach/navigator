"""Translate DTO content into core payload objects."""

from __future__ import annotations

from typing import Iterable, List, Optional

from ..dto.content import Content, Media, Node
from ...core.entity.media import MediaItem, MediaType
from ...core.value.content import Payload
from ...core.policy import classify_media, resolve_caption_policy


def convert(dto: Content) -> Payload:
    """Convert ``Content`` DTOs into domain ``Payload`` objects."""

    text, erase = resolve_caption_policy(
        text=dto.text,
        has_media=bool(dto.media),
        erase_requested=bool(dto.erase),
    )
    return Payload(
        text=text,
        media=_single(dto.media),
        group=_cluster(dto.group),
        reply=dto.reply,
        preview=dto.preview,
        extra=dto.extra,
        erase=erase,
    )


def collect(node: Node) -> List[Payload]:
    """Convert all messages within ``node`` into payloads."""

    return [convert(message) for message in node.messages]


def _single(item: Optional[Media]) -> Optional[MediaItem]:
    """Convert an optional media DTO into a media entity."""

    return _marshal(item) if item else None


def _cluster(items: Optional[Iterable[Media]]) -> Optional[List[MediaItem]]:
    """Convert DTO collections into media entity clusters."""

    if not items:
        return None
    return [_marshal(media) for media in items]


def _marshal(item: Media) -> MediaItem:
    """Build a ``MediaItem`` instance for the provided DTO ``item``."""

    kind = MediaType(item.type) if item.type else classify_media(item.path)
    return MediaItem(type=kind, path=item.path, caption=item.caption)

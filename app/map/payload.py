"""Translate DTO content into core payload objects."""

from __future__ import annotations

from pathlib import Path
from typing import Iterable, List, Optional
from urllib.parse import urlparse

from ..dto.content import Content, Media, Node
from ...core.entity.media import MediaItem, MediaType
from ...core.value.content import Payload

_MEDIA_EXTENSIONS = {
    MediaType.PHOTO: {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"},
    MediaType.VIDEO: {".mp4", ".mov", ".m4v", ".webm"},
    MediaType.AUDIO: {".mp3", ".m4a", ".ogg", ".oga", ".flac", ".wav"},
    MediaType.ANIMATION: {".gif"},
}


def convert(dto: Content) -> Payload:
    """Convert ``Content`` DTOs into domain ``Payload`` objects."""

    text, erase = _resolve_text(dto)
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


def _resolve_text(dto: Content) -> tuple[Optional[str], bool]:
    """Return caption text and erase flag respecting DTO invariants."""

    if not dto.media:
        return dto.text, False
    if dto.erase:
        if dto.text in (None, ""):
            return "", True
        return dto.text, False
    if dto.text == "":
        raise ValueError("empty_caption_without_erase_flag")
    return dto.text, False


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

    kind = MediaType(item.type) if item.type else _classify(item.path)
    return MediaItem(type=kind, path=item.path, caption=item.caption)


def _classify(path: object) -> MediaType:
    """Infer media type by inspecting the ``path`` representation."""

    name = _extract_name(path).lower()
    extension = Path(name).suffix.lower()
    for kind, suffixes in _MEDIA_EXTENSIONS.items():
        if extension in suffixes:
            return kind
    return MediaType.DOCUMENT


def _extract_name(candidate: object) -> str:
    """Return a best-effort filename for ``candidate`` objects."""

    for attribute in ("filename", "file_name", "name"):
        value = getattr(candidate, attribute, None)
        if isinstance(value, str) and value:
            return value
    path = getattr(candidate, "path", None)
    if path and hasattr(path, "name"):
        return str(path.name)
    if isinstance(candidate, str):
        parsed = urlparse(candidate)
        if parsed.scheme in {"http", "https"} and parsed.path:
            return Path(parsed.path).name
        return candidate
    return ""

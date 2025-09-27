"""Policies related to payload caption handling and media classification."""
from __future__ import annotations

from pathlib import Path
from typing import Mapping
from urllib.parse import urlparse

from ..entity.media import MediaType

_MEDIA_EXTENSIONS: Mapping[MediaType, frozenset[str]] = {
    MediaType.PHOTO: frozenset({".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}),
    MediaType.VIDEO: frozenset({".mp4", ".mov", ".m4v", ".webm"}),
    MediaType.AUDIO: frozenset({".mp3", ".m4a", ".ogg", ".oga", ".flac", ".wav"}),
    MediaType.ANIMATION: frozenset({".gif"}),
}


def resolve_caption_policy(
    *,
    text: str | None,
    has_media: bool,
    erase_requested: bool,
) -> tuple[str | None, bool]:
    """Return caption text and erase flag respecting domain invariants."""

    if not has_media:
        return text, False
    if erase_requested:
        if text in (None, ""):
            return "", True
        return text, False
    if text == "":
        raise ValueError("empty_caption_without_erase_flag")
    return text, False


def classify_media(path: object) -> MediaType:
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


__all__ = ["classify_media", "resolve_caption_policy"]

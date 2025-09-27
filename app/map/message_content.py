"""Utilities resolving message content artefacts from metadata."""
from __future__ import annotations

from typing import Iterable, List, Optional, Tuple

from ...core.entity.media import MediaItem, MediaType
from ...core.error import (
    MetadataGroupMediumMissing,
    MetadataKindUnsupported,
    MetadataMediumMissing,
)
from ...core.typing.result import GroupMeta, MediaMeta, Meta, TextMeta
from ...core.value.content import Payload


class MessageContentResolver:
    """Resolve message artefacts derived from rendering metadata."""

    def __init__(self, payload: Payload) -> None:
        self._payload = payload

    def resolve(
        self, meta: Meta
    ) -> Tuple[Optional[str], Optional[MediaItem], Optional[List[MediaItem]]]:
        if isinstance(meta, TextMeta):
            return meta.text, None, None
        if isinstance(meta, MediaMeta):
            return None, self._media_item(meta), None
        if isinstance(meta, GroupMeta):
            return None, None, self._group_items(meta)
        raise MetadataKindUnsupported(getattr(meta, "kind", None))

    def _media_item(self, meta: MediaMeta) -> MediaItem:
        variant = meta.medium
        if self._payload.media:
            return MediaItem(
                type=self._payload.media.type,
                path=meta.file,
                caption=meta.caption,
            )
        if isinstance(variant, str):
            return MediaItem(
                type=MediaType(variant),
                path=meta.file,
                caption=meta.caption,
            )
        raise MetadataMediumMissing()

    def _group_items(self, meta: GroupMeta) -> List[MediaItem]:
        items: List[MediaItem] = []
        for cluster in meta.clusters:
            variant = cluster.medium
            if not isinstance(variant, str):
                raise MetadataGroupMediumMissing()
            items.append(
                MediaItem(
                    type=MediaType(variant),
                    path=cluster.file,
                    caption=cluster.caption,
                )
            )
        return items


class CaptionLengthCalculator:
    """Calculate caption length for sanitising entity spans."""

    @staticmethod
    def calculate(
        text: Optional[str],
        media: Optional[MediaItem],
        group: Optional[Iterable[MediaItem]],
    ) -> int:
        if group:
            first = next(iter(group), None)
            return len(getattr(first, "caption", None) or "") if first else 0
        if media:
            return len(getattr(media, "caption", None) or "")
        return len(text or "")


def resolve_inline(meta: Meta) -> Optional[bool]:
    """Return inline flag derived from metadata if specified."""

    inline = getattr(meta, "inline", None)
    return bool(inline) if inline is not None else None


__all__ = [
    "CaptionLengthCalculator",
    "MessageContentResolver",
    "resolve_inline",
]

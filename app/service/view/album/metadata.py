"""Helpers for deriving album metadata representations."""

from __future__ import annotations

from typing import Iterable, List

from navigator.core.entity.history import Message
from navigator.core.entity.media import MediaItem
from navigator.core.typing.result import Cluster, GroupMeta


class AlbumMetadataBuilder:
    """Derive lineup identifiers and metadata payloads for albums."""

    def lineup(self, message: Message) -> List[int]:
        """Return identifiers associated with the stored album head."""

        return [int(message.id)] + [int(extra) for extra in (message.extras or [])]

    def clusters(self, items: Iterable[MediaItem]) -> List[Cluster]:
        """Return cluster descriptors for the refreshed album payload."""

        clusters: List[Cluster] = []
        for index, item in enumerate(items):
            caption = item.caption if index == 0 else ""
            clusters.append(
                Cluster(medium=item.type.value, file=item.path, caption=caption)
            )
        return clusters

    def meta(self, *, inline: bool, clusters: List[Cluster]) -> GroupMeta:
        """Build group metadata from inline flag and prepared clusters."""

        return GroupMeta(clusters=clusters, inline=inline)


__all__ = ["AlbumMetadataBuilder"]


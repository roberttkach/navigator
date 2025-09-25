"""Typed metadata structures returned by message gateways."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Literal, Sequence


@dataclass(frozen=True, slots=True)
class Cluster:
    """Descriptor for a media item within a group."""

    medium: str | None
    file: str | None
    caption: str | None


@dataclass(frozen=True, slots=True)
class TextMeta:
    """Metadata describing textual messages."""

    kind: Literal["text"] = "text"
    text: str | None = None
    inline: bool | None = None


@dataclass(frozen=True, slots=True)
class MediaMeta:
    """Metadata describing single media messages."""

    kind: Literal["media"] = "media"
    medium: str | None = None
    file: str | None = None
    caption: str | None = None
    inline: bool | None = None


@dataclass(frozen=True, slots=True)
class GroupMeta:
    """Metadata describing media groups."""

    kind: Literal["group"] = "group"
    clusters: Sequence[Cluster] = ()
    inline: bool | None = None


Meta = TextMeta | MediaMeta | GroupMeta

__all__ = ["Cluster", "GroupMeta", "MediaMeta", "Meta", "TextMeta"]

"""Normalize rendering inputs into comparison-friendly views."""
from __future__ import annotations

from collections.abc import Mapping as MappingView
from dataclasses import dataclass, field
from typing import Any, Optional

from ...entity.markup import Markup
from ...entity.media import MediaItem
from ...value.content import Preview


@dataclass(frozen=True, slots=True)
class NormalizedView:
    """Capture the minimal surface we compare across history entries."""

    text: str | None = None
    media: MediaItem | None = None
    group: tuple[MediaItem, ...] = ()
    reply: Markup | None = None
    extra: Mapping[str, Any] = field(default_factory=dict)
    preview: Preview | None = None

    @property
    def has_group(self) -> bool:
        """Report whether the view represents an album submission."""

        return bool(self.group)

    @property
    def has_media(self) -> bool:
        """Report whether the view carries a single media item."""

        return self.media is not None

    @property
    def is_media_payload(self) -> bool:
        """Report whether the view is backed by media rather than text."""

        return self.has_group or self.has_media


def view_of(source: object | None) -> NormalizedView:
    """Normalize supported message views into a comparison surface."""

    if source is None:
        return NormalizedView()

    text = getattr(source, "text", None)
    media = getattr(source, "media", None)
    group = getattr(source, "group", None) or ()
    if group and not isinstance(group, tuple):
        group = tuple(group)

    reply = getattr(source, "reply", getattr(source, "markup", None))

    extra_value = getattr(source, "extra", None)
    if isinstance(extra_value, MappingView):
        extra = dict(extra_value)
    else:
        extra = {}

    preview = getattr(source, "preview", None)

    return NormalizedView(
        text=text,
        media=media,
        group=group,
        reply=reply,
        extra=extra,
        preview=preview,
    )


def textual_extras(view: NormalizedView) -> dict[str, Any]:
    """Preserve extra fields that influence text rendering semantics."""

    data = view.extra or {}
    snapshot: dict[str, Any] = {}
    if "mode" in data:
        snapshot["mode"] = data["mode"]
    if "entities" in data:
        snapshot["entities"] = data["entities"]
    return snapshot


def text_content(view: NormalizedView) -> Optional[str]:
    """Return trimmed textual content when no media is present."""

    if view.is_media_payload:
        return None
    value = view.text
    return str(value).strip() if value is not None else None


def preview_payload(view: NormalizedView):
    """Expose the preview payload so comparisons stay encapsulated."""

    return view.preview


__all__ = [
    "NormalizedView",
    "preview_payload",
    "text_content",
    "textual_extras",
    "view_of",
]

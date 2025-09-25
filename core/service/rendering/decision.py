"""Decide how to reconcile stored history with incoming payloads."""

from __future__ import annotations

from collections.abc import Mapping as MappingView
from dataclasses import dataclass, field
from enum import Enum, auto
from typing import Any, Mapping, Optional

from .config import RenderingConfig
from .helpers import match
from ...entity.markup import Markup
from ...entity.media import MediaItem, MediaType
from ...port.mediaid import MediaIdentityPolicy
from ...value.content import Payload, Preview, caption


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


class Decision(Enum):
    """Possible reconciliation outcomes for an updated entry."""

    RESEND = auto()
    EDIT_TEXT = auto()
    EDIT_MEDIA_CAPTION = auto()
    EDIT_MEDIA = auto()
    EDIT_MARKUP = auto()
    DELETE_SEND = auto()
    NO_CHANGE = auto()


def _view_of(source: object | None) -> NormalizedView:
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
    extra: Mapping[str, Any]
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


def _textual_extras(view: NormalizedView) -> dict[str, Any]:
    """Preserve extra fields that influence text rendering semantics."""

    data = view.extra or {}
    snapshot: dict[str, Any] = {}
    if "mode" in data:
        snapshot["mode"] = data["mode"]
    if "entities" in data:
        snapshot["entities"] = data["entities"]
    return snapshot


@dataclass(frozen=True, slots=True)
class _CaptionFlag:
    """Capture caption-level options relevant for edits."""

    above: bool


@dataclass(frozen=True, slots=True)
class _MediaFlag:
    """Describe media edit options that require resend safeguards."""

    spoiler: bool
    start: object
    thumb: bool


@dataclass(frozen=True, slots=True)
class _MediaProfile:
    """Bundle caption and media attributes for comparison."""

    caption: _CaptionFlag
    edit: _MediaFlag


def _profile_media(view: NormalizedView, config: RenderingConfig) -> _MediaProfile:
    """Extract mutable media attributes that affect edit compatibility."""

    payload = dict(view.extra or {})
    caption = _CaptionFlag(above=bool(payload.get("show_caption_above_media")))
    start = payload.get("start")
    try:
        start = int(start) if start is not None else None
    except Exception:
        pass
    present = bool((payload.get("thumb") is not None) or payload.get("has_thumb"))
    edit = _MediaFlag(
        spoiler=bool(payload.get("spoiler")),
        start=start,
        thumb=(present if config.thumbguard else False),
    )
    return _MediaProfile(caption=caption, edit=edit)


def _text(view: NormalizedView) -> Optional[str]:
    """Return trimmed textual content when no media is present."""

    if view.is_media_payload:
        return None
    value = view.text
    return str(value).strip() if value is not None else None


def _preview(view: NormalizedView):
    """Expose the preview payload so comparisons stay encapsulated."""

    return view.preview


def _identical(old: NormalizedView, new: NormalizedView, policy: MediaIdentityPolicy) -> bool:
    """Check whether two views refer to the same underlying media file."""

    if not (old.media and new.media):
        return False
    if old.media.type != new.media.type:
        return False
    former = getattr(old.media, "path", None)
    latter = getattr(new.media, "path", None)
    return policy.same(former, latter, type=getattr(old.media.type, "value", ""))


def _requires_delete_send(prior: NormalizedView, fresh: NormalizedView) -> bool:
    """Return ``True`` when reconciliation requires send+delete fallback."""

    if prior.has_group or fresh.has_group:
        return True

    restricted = (MediaType.VOICE, MediaType.VIDEO_NOTE)
    if fresh.media and fresh.media.type in restricted:
        return True
    if prior.media and prior.media.type in restricted:
        return True

    if prior.is_media_payload != fresh.is_media_payload:
        return True

    return False


def _decide_textual(prior: NormalizedView, fresh: NormalizedView) -> Decision:
    """Resolve reconciliation for purely textual payloads."""

    if (_text(prior) or "") == (_text(fresh) or ""):
        if (
                (_textual_extras(prior) != _textual_extras(fresh))
                or (_preview(prior) != _preview(fresh))
        ):
            return Decision.EDIT_TEXT
        aligned = match(prior.reply, fresh.reply)
        return Decision.NO_CHANGE if aligned else Decision.EDIT_MARKUP

    return Decision.EDIT_TEXT


def _decide_media(
        prior: NormalizedView,
        fresh: NormalizedView,
        config: RenderingConfig,
) -> Decision:
    """Resolve reconciliation for payloads carrying media objects."""

    if _identical(prior, fresh, config.identity):
        before = _profile_media(prior, config)
        after = _profile_media(fresh, config)

        if before.edit != after.edit:
            return Decision.EDIT_MEDIA

        if (
                (caption(prior) or "") == (caption(fresh) or "")
                and _textual_extras(prior) == _textual_extras(fresh)
                and before.caption == after.caption
        ):
            aligned = match(prior.reply, fresh.reply)
            return Decision.NO_CHANGE if aligned else Decision.EDIT_MARKUP
        return Decision.EDIT_MEDIA_CAPTION

    return Decision.EDIT_MEDIA


def decide(old: Optional[object], new: Payload, config: RenderingConfig) -> Decision:
    """Select an edit strategy that reconciles history with new content."""

    if not old:
        return Decision.RESEND

    prior = _view_of(old)
    fresh = _view_of(new)

    if _requires_delete_send(prior, fresh):
        return Decision.DELETE_SEND

    if not prior.is_media_payload and not fresh.is_media_payload:
        return _decide_textual(prior, fresh)

    if prior.is_media_payload and fresh.is_media_payload:
        return _decide_media(prior, fresh, config)

    return Decision.NO_CHANGE

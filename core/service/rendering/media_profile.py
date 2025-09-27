"""Media comparison helpers used during rendering decisions."""
from __future__ import annotations

from dataclasses import dataclass

from .normalization import NormalizedView
from .config import RenderingConfig
from ...entity.media import MediaType
from ...port.mediaid import MediaIdentityPolicy


@dataclass(frozen=True, slots=True)
class CaptionFlag:
    """Capture caption-level options relevant for edits."""

    above: bool


@dataclass(frozen=True, slots=True)
class MediaFlag:
    """Describe media edit options that require resend safeguards."""

    spoiler: bool
    start: object
    thumb: bool


@dataclass(frozen=True, slots=True)
class MediaProfile:
    """Bundle caption and media attributes for comparison."""

    caption: CaptionFlag
    edit: MediaFlag


def profile_media(view: NormalizedView, config: RenderingConfig) -> MediaProfile:
    """Extract mutable media attributes that affect edit compatibility."""

    payload = dict(view.extra or {})
    caption = CaptionFlag(above=bool(payload.get("show_caption_above_media")))
    start = payload.get("start")
    try:
        start = int(start) if start is not None else None
    except Exception:  # pragma: no cover - defensive conversion
        pass
    present = bool((payload.get("thumb") is not None) or payload.get("has_thumb"))
    edit = MediaFlag(
        spoiler=bool(payload.get("spoiler")),
        start=start,
        thumb=(present if config.thumbguard else False),
    )
    return MediaProfile(caption=caption, edit=edit)


def identical_media(
    old: NormalizedView,
    new: NormalizedView,
    policy: MediaIdentityPolicy,
) -> bool:
    """Check whether two views refer to the same underlying media file."""

    if not (old.media and new.media):
        return False
    if old.media.type != new.media.type:
        return False
    former = getattr(old.media, "path", None)
    latter = getattr(new.media, "path", None)
    return policy.same(former, latter, type=getattr(old.media.type, "value", ""))


def requires_delete_send(prior: NormalizedView, fresh: NormalizedView) -> bool:
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


__all__ = [
    "CaptionFlag",
    "MediaFlag",
    "MediaProfile",
    "identical_media",
    "profile_media",
    "requires_delete_send",
]

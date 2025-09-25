"""Validate and compare media albums for multi-item submissions."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Literal, Optional, Set

from ...entity.media import MediaItem, MediaType
from ...error import NavigatorError
from ...port.limits import Limits


@dataclass(frozen=True, slots=True)
class AlbumInvalid(NavigatorError):
    """Signal that a payload album violates delivery constraints."""

    empty: bool
    limit: bool
    forbidden: bool
    audio: bool
    document: bool

    def __post_init__(self) -> None:
        super().__init__("group_invalid")


def _audit(items: Optional[Iterable[MediaItem]], *, limits: Limits) -> List[str]:
    """Collect album rule violations for the provided media set."""

    material = list(items or [])
    if not material:
        return ["empty"]

    issues: List[str] = []
    if len(material) < limits.groupmin() or len(material) > limits.groupmax():
        issues.append("limit")

    kinds: Set[MediaType] = {item.type for item in material}
    if kinds & {MediaType.ANIMATION, MediaType.VOICE, MediaType.VIDEO_NOTE}:
        issues.append("forbidden")
    if MediaType.AUDIO in kinds and kinds != {MediaType.AUDIO}:
        issues.append("audio")
    if MediaType.DOCUMENT in kinds and kinds != {MediaType.DOCUMENT}:
        issues.append("document")
    return issues


def validate(items: List[MediaItem], *, limits: Limits) -> None:
    """Reject albums that fail validation by raising an explicit error."""

    issues = _audit(items, limits=limits)
    if issues:
        raise AlbumInvalid(
            empty="empty" in issues,
            limit="limit" in issues,
            forbidden="forbidden" in issues,
            audio="audio" in issues,
            document="document" in issues,
        )


def nature(items: List[MediaItem]) -> Literal["audio", "document", "mixed"]:
    """Classify a group by the dominant media class it contains."""

    kinds = {item.type for item in items or []}
    if kinds == {MediaType.AUDIO}:
        return "audio"
    if kinds == {MediaType.DOCUMENT}:
        return "document"
    return "mixed"


def aligned(old: List[MediaItem], new: List[MediaItem], *, limits: Limits) -> bool:
    """Check whether two albums remain compatible for in-place edits."""

    if len(old) != len(new):
        return False
    mood = nature(old)
    if mood == "audio":
        return all(item.type == MediaType.AUDIO for item in new)
    if mood == "document":
        return all(item.type == MediaType.DOCUMENT for item in new)
    allowed = limits.groupmix()
    return all(item.type.value in allowed for item in new)

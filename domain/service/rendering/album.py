from typing import List, Literal, Optional, Set

from ...entity.media import MediaItem, MediaType
from ...error import NavigatorError
from ...port.limits import Limits


class AlbumInvalid(NavigatorError):
    def __init__(
            self,
            *,
            empty: bool,
            limit: bool,
            forbidden: bool,
            audio: bool,
            document: bool,
    ):
        self.empty = empty
        self.limit = limit
        self.forbidden = forbidden
        self.audio = audio
        self.document = document
        super().__init__("group_invalid")


def _audit(items: Optional[List[MediaItem]], *, limits: Limits) -> List[str]:
    issues: List[str] = []
    if not items:
        issues.append("empty")
        return issues
    if len(items) < limits.album_floor() or len(items) > limits.album_ceiling():
        issues.append("limit")
    kinds: Set[MediaType] = {item.type for item in items}
    if kinds & {MediaType.ANIMATION, MediaType.VOICE, MediaType.VIDEO_NOTE}:
        issues.append("forbidden")
    if MediaType.AUDIO in kinds and kinds != {MediaType.AUDIO}:
        issues.append("audio")
    if MediaType.DOCUMENT in kinds and kinds != {MediaType.DOCUMENT}:
        issues.append("document")
    return issues


def validate(items: List[MediaItem], *, limits: Limits) -> None:
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
    kinds = {item.type for item in items or []}
    if kinds == {MediaType.AUDIO}:
        return "audio"
    if kinds == {MediaType.DOCUMENT}:
        return "document"
    return "mixed"


def aligned(old: List[MediaItem], new: List[MediaItem], *, limits: Limits) -> bool:
    if len(old) != len(new):
        return False
    mood = nature(old)
    if mood == "audio":
        return all(item.type == MediaType.AUDIO for item in new)
    if mood == "document":
        return all(item.type == MediaType.DOCUMENT for item in new)
    allowed = limits.album_blend()
    return all(item.type.value in allowed for item in new)

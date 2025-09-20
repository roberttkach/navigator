from typing import Optional, List, Set, Literal

from ...constants import AlbumBlend, AlbumCeiling, AlbumFloor
from ...entity.media import MediaItem, MediaType
from ...error import NavigatorError


class MediaGroupInvalid(NavigatorError):
    def __init__(
            self,
            *,
            empty: bool,
            invalid_size: bool,
            forbidden_types: bool,
            audio_mixed: bool,
            document_mixed: bool,
    ):
        self.empty = empty
        self.invalid_size = invalid_size
        self.forbidden_types = forbidden_types
        self.audio_mixed = audio_mixed
        self.document_mixed = document_mixed
        super().__init__("group_invalid")


def _group_invalid_reasons(items: Optional[List[MediaItem]]) -> List[str]:
    reasons = []
    if not items:
        reasons.append("empty")
        return reasons
    if len(items) < AlbumFloor or len(items) > AlbumCeiling:
        reasons.append("size")
    types: Set[MediaType] = {i.type for i in items}
    if types & {MediaType.ANIMATION, MediaType.VOICE, MediaType.VIDEO_NOTE}:
        reasons.append("forbidden_types")
    if MediaType.AUDIO in types and types != {MediaType.AUDIO}:
        reasons.append("audio_mixed")
    if MediaType.DOCUMENT in types and types != {MediaType.DOCUMENT}:
        reasons.append("document_mixed")
    return reasons


def validate_group(items: List[MediaItem]) -> None:
    reasons = _group_invalid_reasons(items)
    if reasons:
        raise MediaGroupInvalid(
            empty="empty" in reasons,
            invalid_size="size" in reasons,
            forbidden_types="forbidden_types" in reasons,
            audio_mixed="audio_mixed" in reasons,
            document_mixed="document_mixed" in reasons,
        )


def album_kind(items: List[MediaItem]) -> Literal["audio", "document", "mixed"]:
    types = {i.type for i in items or []}
    if types == {MediaType.AUDIO}:
        return "audio"
    if types == {MediaType.DOCUMENT}:
        return "document"
    return "mixed"


def album_compatible(old: List[MediaItem], new: List[MediaItem]) -> bool:
    if len(old) != len(new):
        return False
    k = album_kind(old)
    if k == "audio":
        return all(i.type == MediaType.AUDIO for i in new)
    if k == "document":
        return all(i.type == MediaType.DOCUMENT for i in new)
    return all(i.type.value in AlbumBlend for i in new)

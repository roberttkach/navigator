from dataclasses import dataclass
from enum import Enum
from typing import Optional


class MediaType(Enum):
    PHOTO = "photo"
    VIDEO = "video"
    DOCUMENT = "document"
    AUDIO = "audio"
    ANIMATION = "animation"
    VOICE = "voice"
    VIDEO_NOTE = "video_note"


@dataclass(frozen=True, slots=True)
class MediaItem:
    type: MediaType
    path: object  # В объектах истории path хранит Telegram file_id; в Payload может быть локал/URLInputFile/str.
    caption: Optional[str] = None

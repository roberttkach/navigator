from pathlib import Path
from typing import List, Optional
from urllib.parse import urlparse

from ..dto.content import Content, Media, Node
from ...domain.entity.media import MediaItem, MediaType
from ...domain.value.content import Payload

_PHOTO = {".jpg", ".jpeg", ".png", ".webp", ".heic", ".heif"}
_VIDEO = {".mp4", ".mov", ".m4v", ".webm"}
_AUDIO = {".mp3", ".m4a", ".ogg", ".oga", ".flac", ".wav"}
_ANIM = {".gif"}


def _name_like(x: object) -> str:
    for attr in ("filename", "file_name", "name"):
        v = getattr(x, attr, None)
        if isinstance(v, str) and v:
            return v
    p = getattr(x, "path", None)
    if p and hasattr(p, "name"):
        return str(p.name)
    if isinstance(x, str):
        try:
            u = urlparse(x)
            if u.scheme in ("http", "https") and u.path:
                return Path(u.path).name
        except Exception:
            pass
        return x
    return ""


def _infer_type(path: object) -> MediaType:
    name = _name_like(path).lower()
    ext = Path(name).suffix.lower()
    if ext in _PHOTO:
        return MediaType.PHOTO
    if ext in _VIDEO:
        return MediaType.VIDEO
    if ext in _AUDIO:
        return MediaType.AUDIO
    if ext in _ANIM:
        return MediaType.ANIMATION
    return MediaType.DOCUMENT


def _convert_media_item(item: Media) -> MediaItem:
    mtype = MediaType(item.type) if item.type else _infer_type(item.path)
    return MediaItem(type=mtype, path=item.path, caption=item.caption)


def _to_media(item: Optional[Media]) -> Optional[MediaItem]:
    if not item:
        return None
    return _convert_media_item(item)


def _to_group(items: Optional[List[Media]]) -> Optional[List[MediaItem]]:
    if not items:
        return None
    return [_convert_media_item(i) for i in items]


def to_payload(dto: Content) -> Payload:
    # При media и clear_caption=True — выставляем text="" для явной очистки подписи.
    text = dto.text
    clear_caption = False
    if dto.media and dto.clear_caption:
        if text is None or text == "":
            text = ""
            clear_caption = True
        else:
            clear_caption = False
    if dto.media and text == "" and not dto.clear_caption:
        raise ValueError("empty_caption_without_clear_flag")
    return Payload(
        text=text,
        media=_to_media(dto.media),
        group=_to_group(dto.group),
        reply=dto.reply,
        preview=dto.preview,
        extra=dto.extra,
        clear_caption=clear_caption,
    )


def to_node_payload(node: Node) -> List[Payload]:
    return [to_payload(m) for m in node.messages]

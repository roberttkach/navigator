from __future__ import annotations

import logging
from typing import List, Union, Dict, Any

from aiogram.types import (
    FSInputFile,
    BufferedInputFile,
    URLInputFile,
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
    InputMediaAudio,
    InputMediaAnimation,
)

from .extra import audit, ALLOWED_MEDIA_EXTRA
from .screen import screen
from .serializer import cleanse, divide
from ...domain.constants import CaptionLimit
from ...domain.entity.media import MediaItem, MediaType
from ...domain.error import MessageEditForbidden, NavigatorError, CaptionTooLong
from ...domain.log.emit import jlog
from ...domain.service.rendering.album import MediaGroupInvalid, validate
from ...domain.util.path import local, remote
from ...domain.log.code import LogCode

InputFile = Union[str, FSInputFile, BufferedInputFile, URLInputFile]
InputMedia = Union[InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio, InputMediaAnimation]

logger = logging.getLogger(__name__)


def weblink(obj) -> bool:
    """True для aiogram.types.URLInputFile."""
    return isinstance(obj, URLInputFile)


def adapt(x: object, *, native: bool) -> InputFile:
    if not isinstance(x, (FSInputFile, BufferedInputFile, URLInputFile, str)):
        raise ValueError("unsupported input file descriptor")
    s = x
    if isinstance(s, str) and remote(s):
        return URLInputFile(s)
    if isinstance(s, str) and local(s):
        if not native:
            raise MessageEditForbidden("inline_local_path_forbidden")
        return FSInputFile(s)
    return s


def convert(item: MediaItem, *, native: bool) -> InputFile:
    return adapt(item.path, native=native)


def _screen(extra: Dict[str, Any] | None) -> None:
    audit(extra, ALLOWED_MEDIA_EXTRA)


def compose(
        item: MediaItem,
        caption: str | None = None,
        *,
        extra: Dict[str, Any] | None = None,
        native: bool = True,
        truncate: bool = False,
) -> InputMedia:
    catalog = {
        MediaType.PHOTO: InputMediaPhoto,
        MediaType.VIDEO: InputMediaVideo,
        MediaType.DOCUMENT: InputMediaDocument,
        MediaType.AUDIO: InputMediaAudio,
        MediaType.ANIMATION: InputMediaAnimation,
    }
    handler = catalog.get(item.type)
    if not handler:
        jlog(logger, logging.WARNING, LogCode.MEDIA_UNSUPPORTED, kind=str(getattr(item.type, "value", None)))
        if item.type in (MediaType.VOICE, MediaType.VIDEO_NOTE):
            raise MessageEditForbidden("edit_media_type_forbidden")
        raise ValueError(f"Unsupported media type for InputMedia: {item.type}")
    bundle = divide(extra)
    _screen(bundle["media"])
    caption = caption if caption is not None else item.caption
    length = len(caption or "")
    mapping = cleanse(bundle["caption"], captioning=True, target=handler, length=length)
    settings = bundle["media"] or {}
    if item.type in (MediaType.PHOTO, MediaType.VIDEO, MediaType.ANIMATION):
        if settings.get("spoiler") is not None:
            mapping["has_spoiler"] = bool(settings.get("spoiler"))
        if settings.get("show_caption_above_media") is not None:
            mapping["show_caption_above_media"] = bool(settings.get("show_caption_above_media"))
    if item.type == MediaType.VIDEO:
        if settings.get("start") is not None:
            mapping["start_timestamp"] = settings.get("start")
    if item.type in (MediaType.VIDEO, MediaType.ANIMATION, MediaType.AUDIO, MediaType.DOCUMENT):
        if settings.get("thumb") is not None:
            mapping["thumbnail"] = adapt(settings.get("thumb"), native=native)
    if item.type == MediaType.AUDIO:
        if settings.get("title") is not None:
            mapping["title"] = str(settings.get("title"))
        if settings.get("performer") is not None:
            mapping["performer"] = str(settings.get("performer"))
        if settings.get("duration") is not None:
            mapping["duration"] = int(settings.get("duration"))
    if item.type in (MediaType.VIDEO, MediaType.ANIMATION):
        if settings.get("width") is not None:
            mapping["width"] = int(settings.get("width"))
        if settings.get("height") is not None:
            mapping["height"] = int(settings.get("height"))
        if settings.get("duration") is not None:
            mapping["duration"] = int(settings.get("duration"))

    if caption is not None and len(str(caption)) > CaptionLimit:
        if truncate:
            caption = str(caption)[:CaptionLimit]
        else:
            raise CaptionTooLong()

    mapping = screen(handler, mapping)
    arguments = {"media": convert(item, native=native), **mapping}
    if caption is not None:
        arguments["caption"] = caption
    return handler(**arguments)


def assemble(items: List[MediaItem], extra: Dict[str, Any] | None = None, *, native: bool = True,
             truncate: bool = False) -> List[InputMedia]:
    kinds = [getattr(i.type, "value", None) for i in (items or [])]
    try:
        validate(items)
    except NavigatorError as e:
        if isinstance(e, MediaGroupInvalid):
            jlog(
                logger,
                logging.WARNING,
                LogCode.MEDIA_UNSUPPORTED,
                kind="group_invalid",
                flags={
                    "empty": e.empty,
                    "limit": e.limit,
                    "forbidden": e.forbidden,
                    "audio": e.audio,
                    "document": e.document,
                },
                types=kinds,
            )
        else:
            jlog(logger, logging.WARNING, LogCode.MEDIA_UNSUPPORTED, kind="group_invalid", types=kinds)
        raise
    result: List[InputMedia] = []
    for index, item in enumerate(items):
        caption = item.caption if index == 0 else ""
        result.append(compose(item, caption=caption, extra=extra, native=native, truncate=truncate))
    return result

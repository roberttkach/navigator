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

from .extra import validate_extra, ALLOWED_MEDIA_EXTRA
from .keyfilter import accept_for
from .serializer import sanitize_text_kwargs, split_extra
from ...domain.constants import CAPTION_MAX
from ...domain.entity.media import MediaItem, MediaType
from ...domain.error import MessageEditForbidden, NavigatorError, CaptionTooLong
from ...domain.log.emit import jlog
from ...domain.service.rendering.album import validate_group, MediaGroupInvalid
from ...domain.util.path import is_http_url, is_local_path
from ...domain.log.code import LogCode

InputFile = Union[str, FSInputFile, BufferedInputFile, URLInputFile]
InputMedia = Union[InputMediaPhoto, InputMediaVideo, InputMediaDocument, InputMediaAudio, InputMediaAnimation]

logger = logging.getLogger(__name__)


def is_url_input_file(obj) -> bool:
    """True для aiogram.types.URLInputFile."""
    return isinstance(obj, URLInputFile)


def as_input_file(x: object, *, allow_local: bool) -> InputFile:
    if not isinstance(x, (FSInputFile, BufferedInputFile, URLInputFile, str)):
        raise ValueError("unsupported input file descriptor")
    s = x
    if isinstance(s, str) and is_http_url(s):
        return URLInputFile(s)
    if isinstance(s, str) and is_local_path(s):
        if not allow_local:
            raise MessageEditForbidden("inline_local_path_forbidden")
        return FSInputFile(s)
    return s


def to_input_file(item: MediaItem, *, allow_local: bool) -> InputFile:
    return as_input_file(item.path, allow_local=allow_local)


def _validate_media_extra(extra: Dict[str, Any] | None) -> None:
    validate_extra(extra, ALLOWED_MEDIA_EXTRA)


def to_input_media(
        item: MediaItem,
        caption: str | None = None,
        *,
        extra: Dict[str, Any] | None = None,
        allow_local: bool = True,
        truncate: bool = False,
) -> InputMedia:
    media_map = {
        MediaType.PHOTO: InputMediaPhoto,
        MediaType.VIDEO: InputMediaVideo,
        MediaType.DOCUMENT: InputMediaDocument,
        MediaType.AUDIO: InputMediaAudio,
        MediaType.ANIMATION: InputMediaAnimation,
    }
    input_class = media_map.get(item.type)
    if not input_class:
        jlog(logger, logging.WARNING, LogCode.MEDIA_UNSUPPORTED, kind=str(getattr(item.type, "value", None)))
        if item.type in (MediaType.VOICE, MediaType.VIDEO_NOTE):
            raise MessageEditForbidden("edit_media_type_forbidden")
        raise ValueError(f"Unsupported media type for InputMedia: {item.type}")
    cap_extra, media_extra = split_extra(extra)
    _validate_media_extra(media_extra)
    cap = caption if caption is not None else item.caption
    txt_len = len(cap or "")
    kv = sanitize_text_kwargs(cap_extra, is_caption=True, target=input_class, text_len=txt_len)
    opts = media_extra or {}
    if item.type in (MediaType.PHOTO, MediaType.VIDEO, MediaType.ANIMATION):
        if opts.get("spoiler") is not None:
            kv["has_spoiler"] = bool(opts.get("spoiler"))
        if opts.get("show_caption_above_media") is not None:
            kv["show_caption_above_media"] = bool(opts.get("show_caption_above_media"))
    if item.type == MediaType.VIDEO:
        if opts.get("start") is not None:
            kv["start_timestamp"] = opts.get("start")
    if item.type in (MediaType.VIDEO, MediaType.ANIMATION, MediaType.AUDIO, MediaType.DOCUMENT):
        if opts.get("thumb") is not None:
            kv["thumbnail"] = as_input_file(opts.get("thumb"), allow_local=allow_local)

    # поля InputMedia*
    if item.type == MediaType.AUDIO:
        if opts.get("title") is not None:
            kv["title"] = str(opts.get("title"))
        if opts.get("performer") is not None:
            kv["performer"] = str(opts.get("performer"))
        if opts.get("duration") is not None:
            kv["duration"] = int(opts.get("duration"))
    if item.type in (MediaType.VIDEO, MediaType.ANIMATION):
        if opts.get("width") is not None:
            kv["width"] = int(opts.get("width"))
        if opts.get("height") is not None:
            kv["height"] = int(opts.get("height"))
        if opts.get("duration") is not None:
            kv["duration"] = int(opts.get("duration"))

    if cap is not None and len(str(cap)) > CAPTION_MAX:
        if truncate:
            cap = str(cap)[:CAPTION_MAX]
        else:
            raise CaptionTooLong()
    # Фильтрация ключей под сигнатуру конкретного InputMedia* класса
    kv = accept_for(input_class, kv)
    kwargs = {"media": to_input_file(item, allow_local=allow_local), **kv}
    if cap is not None:
        kwargs["caption"] = cap
    return input_class(**kwargs)


def group_to_input(items: List[MediaItem], extra: Dict[str, Any] | None = None, *, allow_local: bool = True,
                   truncate: bool = False) -> List[InputMedia]:
    kinds = [getattr(i.type, "value", None) for i in (items or [])]
    try:
        validate_group(items)
    except NavigatorError as e:
        if isinstance(e, MediaGroupInvalid):
            jlog(
                logger,
                logging.WARNING,
                LogCode.MEDIA_UNSUPPORTED,
                kind="group_invalid",
                flags={
                    "empty": e.empty,
                    "size": e.invalid_size,
                    "forbidden_types": e.forbidden_types,
                    "audio_mixed": e.audio_mixed,
                    "document_mixed": e.document_mixed,
                },
                types=kinds,
            )
        else:
            jlog(logger, logging.WARNING, LogCode.MEDIA_UNSUPPORTED, kind="group_invalid", types=kinds)
        raise
    out: List[InputMedia] = []
    for idx, item in enumerate(items):
        cap = item.caption if idx == 0 else ""
        out.append(to_input_media(item, caption=cap, extra=extra, allow_local=allow_local, truncate=truncate))
    return out

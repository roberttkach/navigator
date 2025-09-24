from __future__ import annotations

import logging
import re
from typing import Dict, List, Union

from aiogram.types import (
    BufferedInputFile,
    FSInputFile,
    InputMediaAnimation,
    InputMediaAudio,
    InputMediaDocument,
    InputMediaPhoto,
    InputMediaVideo,
    URLInputFile,
)

from navigator.domain.entity.media import MediaItem, MediaType
from navigator.domain.error import CaptionOverflow, EditForbidden, NavigatorError
from navigator.logging import LogCode, jlog
from navigator.domain.port.limits import Limits
from navigator.domain.port.pathpolicy import MediaPathPolicy
from navigator.domain.service.rendering.album import validate
from navigator.domain.util.path import local, remote

from .serializer.screen import SignatureScreen

InputFile = Union[str, FSInputFile, BufferedInputFile, URLInputFile]
InputMedia = Union[
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
    InputMediaAudio,
    InputMediaAnimation,
]

logger = logging.getLogger(__name__)

_FILE_ID_RE = re.compile(r"^[A-Za-z0-9_.:\-=]{20,}$")


class TelegramMediaPolicy(MediaPathPolicy):
    def __init__(self, *, strict: bool = True) -> None:
        self._strict = strict

    def admissible(self, path: object, *, inline: bool) -> bool:
        if not inline:
            return True
        if isinstance(path, URLInputFile):
            return True
        if isinstance(path, str):
            if remote(path):
                return True
            if local(path):
                return False
            if self._strict:
                return bool(_FILE_ID_RE.match(path))
            return True
        return False

    def adapt(self, path: object, *, native: bool) -> object:
        if isinstance(path, (BufferedInputFile, URLInputFile)):
            return path
        if isinstance(path, FSInputFile):
            if not native:
                raise EditForbidden("inline_local_path_forbidden")
            return path
        if isinstance(path, str):
            if remote(path):
                return URLInputFile(path)
            if local(path):
                if not native:
                    raise EditForbidden("inline_local_path_forbidden")
                return FSInputFile(path)
            return path
        return path


def convert(item: MediaItem, *, policy: MediaPathPolicy, native: bool) -> InputFile:
    return policy.adapt(item.path, native=native)


def _media_handler(item: MediaItem):
    catalog = {
        MediaType.PHOTO: InputMediaPhoto,
        MediaType.VIDEO: InputMediaVideo,
        MediaType.DOCUMENT: InputMediaDocument,
        MediaType.AUDIO: InputMediaAudio,
        MediaType.ANIMATION: InputMediaAnimation,
    }
    handler = catalog.get(item.type)
    if handler is None:
        if item.type in (MediaType.VOICE, MediaType.VIDEO_NOTE):
            raise EditForbidden("edit_media_type_forbidden")
        raise ValueError(f"unsupported media type: {item.type}")
    return handler


def compose(
    item: MediaItem,
    *,
    caption: str | None,
    caption_extra: Dict[str, object],
    media_extra: Dict[str, object],
    policy: MediaPathPolicy,
    screen: SignatureScreen,
    limits: Limits,
    native: bool,
) -> InputMedia:
    handler = _media_handler(item)
    mapping: Dict[str, object] = {}

    if caption is not None:
        if len(str(caption)) > limits.caption_max():
            raise CaptionOverflow()
        mapping["caption"] = caption

    filtered_caption = screen.filter(handler, caption_extra)
    mapping.update(filtered_caption)

    settings: Dict[str, object] = {}
    if media_extra.get("spoiler") is not None:
        settings["has_spoiler"] = bool(media_extra.get("spoiler"))
    if media_extra.get("show_caption_above_media") is not None:
        settings["show_caption_above_media"] = bool(media_extra.get("show_caption_above_media"))
    if media_extra.get("start") is not None:
        settings["start_timestamp"] = media_extra.get("start")
    if media_extra.get("supports_streaming") is not None:
        settings["supports_streaming"] = bool(media_extra.get("supports_streaming"))

    if media_extra.get("cover") is not None:
        settings["cover"] = policy.adapt(media_extra.get("cover"), native=native)
    if media_extra.get("thumb") is not None:
        settings["thumbnail"] = policy.adapt(media_extra.get("thumb"), native=native)

    if media_extra.get("title") is not None:
        settings["title"] = str(media_extra.get("title"))
    if media_extra.get("performer") is not None:
        settings["performer"] = str(media_extra.get("performer"))
    if media_extra.get("duration") is not None:
        settings["duration"] = int(media_extra.get("duration"))

    if media_extra.get("width") is not None:
        settings["width"] = int(media_extra.get("width"))
    if media_extra.get("height") is not None:
        settings["height"] = int(media_extra.get("height"))

    filtered_settings = screen.filter(handler, settings)
    mapping.update(filtered_settings)

    arguments = {"media": convert(item, policy=policy, native=native), **mapping}
    return handler(**arguments)


def assemble(
    items: List[MediaItem],
    *,
    caption_extra: Dict[str, object],
    media_extra: Dict[str, object],
    policy: MediaPathPolicy,
    screen: SignatureScreen,
    limits: Limits,
    native: bool,
) -> List[InputMedia]:
    kinds = [getattr(i.type, "value", None) for i in (items or [])]
    try:
        validate(items, limits=limits)
    except NavigatorError as exc:
        jlog(
            logger,
            logging.WARNING,
            LogCode.MEDIA_UNSUPPORTED,
            kind="group_invalid",
            types=kinds,
        )
        raise exc

    result: List[InputMedia] = []
    for index, item in enumerate(items):
        text = item.caption if index == 0 else ""
        result.append(
            compose(
                item,
                caption=text,
                caption_extra=caption_extra,
                media_extra=media_extra,
                policy=policy,
                screen=screen,
                limits=limits,
                native=native,
            )
        )
    return result


__all__ = ["TelegramMediaPolicy", "convert", "compose", "assemble"]

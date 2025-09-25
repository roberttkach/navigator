from __future__ import annotations

import logging
import re
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
from navigator.core.entity.media import MediaItem, MediaType
from navigator.core.error import CaptionOverflow, EditForbidden, NavigatorError
from navigator.core.port.limits import Limits
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.service.rendering.album import validate
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.util.path import local, remote
from typing import Dict, List, Union

from .serializer.screen import SignatureScreen

InputFile = Union[str, FSInputFile, BufferedInputFile, URLInputFile]
InputMedia = Union[
    InputMediaPhoto,
    InputMediaVideo,
    InputMediaDocument,
    InputMediaAudio,
    InputMediaAnimation,
]

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


def _select(item: MediaItem):
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
        captionmeta: Dict[str, object],
        mediameta: Dict[str, object],
        policy: MediaPathPolicy,
        screen: SignatureScreen,
        limits: Limits,
        native: bool,
) -> InputMedia:
    handler = _select(item)
    mapping: Dict[str, object] = {}

    if caption is not None:
        if len(str(caption)) > limits.captionlimit():
            raise CaptionOverflow()
        mapping["caption"] = caption

    captionview = screen.filter(handler, captionmeta)
    mapping.update(captionview)

    settings: Dict[str, object] = {}
    if mediameta.get("spoiler") is not None:
        settings["has_spoiler"] = bool(mediameta.get("spoiler"))
    if mediameta.get("show_caption_above_media") is not None:
        settings["show_caption_above_media"] = bool(mediameta.get("show_caption_above_media"))
    if mediameta.get("start") is not None:
        settings["start_timestamp"] = mediameta.get("start")
    if mediameta.get("supports_streaming") is not None:
        settings["supports_streaming"] = bool(mediameta.get("supports_streaming"))

    if mediameta.get("cover") is not None:
        settings["cover"] = policy.adapt(mediameta.get("cover"), native=native)
    if mediameta.get("thumb") is not None:
        settings["thumbnail"] = policy.adapt(mediameta.get("thumb"), native=native)

    if mediameta.get("title") is not None:
        settings["title"] = str(mediameta.get("title"))
    if mediameta.get("performer") is not None:
        settings["performer"] = str(mediameta.get("performer"))
    if mediameta.get("duration") is not None:
        settings["duration"] = int(mediameta.get("duration"))

    if mediameta.get("width") is not None:
        settings["width"] = int(mediameta.get("width"))
    if mediameta.get("height") is not None:
        settings["height"] = int(mediameta.get("height"))

    settingview = screen.filter(handler, settings)
    mapping.update(settingview)

    arguments = {"media": convert(item, policy=policy, native=native), **mapping}
    return handler(**arguments)


def assemble(
        items: List[MediaItem],
        *,
        captionmeta: Dict[str, object],
        mediameta: Dict[str, object],
        policy: MediaPathPolicy,
        screen: SignatureScreen,
        limits: Limits,
        native: bool,
        telemetry: Telemetry | None = None,
) -> List[InputMedia]:
    channel: TelemetryChannel | None = (
        telemetry.channel(__name__) if telemetry else None
    )
    kinds = [getattr(i.type, "value", None) for i in (items or [])]
    try:
        validate(items, limits=limits)
    except NavigatorError as exc:
        if channel is not None:
            channel.emit(
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
                captionmeta=captionmeta,
                mediameta=mediameta,
                policy=policy,
                screen=screen,
                limits=limits,
                native=native,
            )
        )
    return result


__all__ = ["TelegramMediaPolicy", "convert", "compose", "assemble"]

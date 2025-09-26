"""Telegram media type aliases and helper selectors."""

from __future__ import annotations

from collections.abc import Mapping

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
from navigator.core.error import EditForbidden

InputFile = str | FSInputFile | BufferedInputFile | URLInputFile
InputMedia = (
    InputMediaPhoto
    | InputMediaVideo
    | InputMediaDocument
    | InputMediaAudio
    | InputMediaAnimation
)

_MEDIA_TYPE_HANDLERS: Mapping[MediaType, type[InputMedia]] = {
    MediaType.PHOTO: InputMediaPhoto,
    MediaType.VIDEO: InputMediaVideo,
    MediaType.DOCUMENT: InputMediaDocument,
    MediaType.AUDIO: InputMediaAudio,
    MediaType.ANIMATION: InputMediaAnimation,
}


def select_handler(item: MediaItem) -> type[InputMedia]:
    """Return appropriate Telegram handler for ``item`` type."""

    handler = _MEDIA_TYPE_HANDLERS.get(item.type)
    if handler is None:
        if item.type in (MediaType.VOICE, MediaType.VIDEO_NOTE):
            raise EditForbidden("edit_media_type_forbidden")
        raise ValueError(f"unsupported media type: {item.type}")
    return handler


__all__ = [
    "BufferedInputFile",
    "FSInputFile",
    "InputFile",
    "InputMedia",
    "InputMediaAnimation",
    "InputMediaAudio",
    "InputMediaDocument",
    "InputMediaPhoto",
    "InputMediaVideo",
    "URLInputFile",
    "select_handler",
]

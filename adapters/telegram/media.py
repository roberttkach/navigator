"""Provide Telegram media conversion helpers for Navigator payloads."""

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
from collections.abc import Mapping
from navigator.core.entity.media import MediaItem, MediaType
from navigator.core.error import CaptionOverflow, EditForbidden, NavigatorError
from navigator.core.port.limits import Limits
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.service.rendering.album import validate
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.util.path import local, remote

from .serializer.screen import SignatureScreen

InputFile = str | FSInputFile | BufferedInputFile | URLInputFile
InputMedia = (
        InputMediaPhoto
        | InputMediaVideo
        | InputMediaDocument
        | InputMediaAudio
        | InputMediaAnimation
)

_FILE_ID_RE = re.compile(r"^[A-Za-z0-9_.:\-=]{20,}$")
_MEDIA_TYPE_HANDLERS: Mapping[MediaType, type[InputMedia]] = {
    MediaType.PHOTO: InputMediaPhoto,
    MediaType.VIDEO: InputMediaVideo,
    MediaType.DOCUMENT: InputMediaDocument,
    MediaType.AUDIO: InputMediaAudio,
    MediaType.ANIMATION: InputMediaAnimation,
}
_BOOLEAN_SETTINGS = {
    "spoiler": "has_spoiler",
    "show_caption_above_media": "show_caption_above_media",
    "supports_streaming": "supports_streaming",
}
_STRING_SETTINGS = {
    "title": "title",
    "performer": "performer",
}
_INTEGER_SETTINGS = {
    "duration": "duration",
    "width": "width",
    "height": "height",
}
_TIMESTAMP_FIELDS = {"start": "start_timestamp"}
_PATH_SETTINGS = {
    "cover": "cover",
    "thumb": "thumbnail",
}


class TelegramMediaPolicy(MediaPathPolicy):
    """Enforce media path policies for Telegram transports."""

    def __init__(self, *, strict: bool = True) -> None:
        self._strict = strict

    def admissible(self, path: object, *, inline: bool) -> bool:
        """Return ``True`` when ``path`` may be used for inline uploads."""

        if not inline:
            return True
        if isinstance(path, URLInputFile):
            return True
        if not isinstance(path, str):
            return False
        if remote(path):
            return True
        if local(path):
            return False
        return bool(_FILE_ID_RE.match(path)) if self._strict else True

    def adapt(self, path: object, *, native: bool) -> object:
        """Return a Telegram-compatible input for ``path`` respecting flags."""

        if isinstance(path, BufferedInputFile | URLInputFile):
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
    """Return Telegram input file representation for ``item``."""

    return policy.adapt(item.path, native=native)


def compose(
        item: MediaItem,
        *,
        caption: str | None,
        captionmeta: dict[str, object],
        mediameta: dict[str, object],
        policy: MediaPathPolicy,
        screen: SignatureScreen,
        limits: Limits,
        native: bool,
) -> InputMedia:
    """Compose Telegram media objects enriched with Navigator metadata."""

    handler = _select(item)
    mapping: dict[str, object] = {}

    if caption is not None:
        if len(str(caption)) > limits.captionlimit():
            raise CaptionOverflow()
        mapping["caption"] = caption

    mapping.update(screen.filter(handler, captionmeta))
    mapping.update(_prepare_media_settings(mediameta, policy, native, handler, screen))

    arguments = {"media": convert(item, policy=policy, native=native), **mapping}
    return handler(**arguments)


def assemble(
        items: list[MediaItem],
        *,
        captionmeta: dict[str, object],
        mediameta: dict[str, object],
        policy: MediaPathPolicy,
        screen: SignatureScreen,
        limits: Limits,
        native: bool,
        telemetry: Telemetry | None = None,
) -> list[InputMedia]:
    """Compose album media structures for Telegram dispatch."""

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

    result: list[InputMedia] = []
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


def _select(item: MediaItem) -> type[InputMedia]:
    """Return appropriate Telegram handler for ``item`` type."""

    handler = _MEDIA_TYPE_HANDLERS.get(item.type)
    if handler is None:
        if item.type in (MediaType.VOICE, MediaType.VIDEO_NOTE):
            raise EditForbidden("edit_media_type_forbidden")
        raise ValueError(f"unsupported media type: {item.type}")
    return handler


def _prepare_media_settings(
        mediameta: Mapping[str, object],
        policy: MediaPathPolicy,
        native: bool,
        handler: type[InputMedia],
        screen: SignatureScreen,
) -> dict[str, object]:
    """Normalise optional media metadata into Telegram-friendly keys."""

    settings: dict[str, object] = {}
    settings.update(_collect_boolean_flags(mediameta))
    settings.update(_collect_string_fields(mediameta))
    settings.update(_collect_integer_fields(mediameta))
    settings.update(_collect_timestamp_fields(mediameta))
    settings.update(_collect_path_fields(mediameta, policy, native))
    filtered = screen.filter(handler, settings)
    return filtered


def _collect_boolean_flags(mediameta: Mapping[str, object]) -> dict[str, object]:
    """Return boolean settings recognised by Telegram APIs."""

    payload: dict[str, object] = {}
    for key, target in _BOOLEAN_SETTINGS.items():
        if key in mediameta and mediameta[key] is not None:
            payload[target] = bool(mediameta[key])
    return payload


def _collect_string_fields(mediameta: Mapping[str, object]) -> dict[str, object]:
    """Return string metadata prepared for Telegram models."""

    payload: dict[str, object] = {}
    for key, target in _STRING_SETTINGS.items():
        value = mediameta.get(key)
        if value is not None:
            payload[target] = str(value)
    return payload


def _collect_integer_fields(mediameta: Mapping[str, object]) -> dict[str, object]:
    """Return integer metadata prepared for Telegram models."""

    payload: dict[str, object] = {}
    for key, target in _INTEGER_SETTINGS.items():
        value = mediameta.get(key)
        if value is not None:
            payload[target] = int(value)
    return payload


def _collect_timestamp_fields(mediameta: Mapping[str, object]) -> dict[str, object]:
    """Return timestamp-like metadata prepared for Telegram models."""

    payload: dict[str, object] = {}
    for key, target in _TIMESTAMP_FIELDS.items():
        value = mediameta.get(key)
        if value is not None:
            payload[target] = value
    return payload


def _collect_path_fields(
        mediameta: Mapping[str, object],
        policy: MediaPathPolicy,
        native: bool,
) -> dict[str, object]:
    """Return path-like metadata adapted for Telegram transport rules."""

    payload: dict[str, object] = {}
    for key, target in _PATH_SETTINGS.items():
        value = mediameta.get(key)
        if value is not None:
            payload[target] = policy.adapt(value, native=native)
    return payload


__all__ = ["TelegramMediaPolicy", "convert", "compose", "assemble"]

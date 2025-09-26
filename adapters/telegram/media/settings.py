"""Normalisation of Telegram media metadata settings."""

from __future__ import annotations

from collections.abc import Mapping

from navigator.core.port.pathpolicy import MediaPathPolicy

from ..serializer.screen import SignatureScreen

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


class MediaSettingsNormalizer:
    """Normalise optional metadata for Telegram media handlers."""

    def __init__(self, policy: MediaPathPolicy, screen: SignatureScreen) -> None:
        self._policy = policy
        self._screen = screen

    def prepare(
        self,
        mediameta: Mapping[str, object],
        *,
        native: bool,
        handler: type,
    ) -> dict[str, object]:
        settings: dict[str, object] = {}
        settings.update(_collect_boolean_flags(mediameta))
        settings.update(_collect_string_fields(mediameta))
        settings.update(_collect_integer_fields(mediameta))
        settings.update(_collect_timestamp_fields(mediameta))
        settings.update(_collect_path_fields(mediameta, self._policy, native))
        return self._screen.filter(handler, settings)


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


__all__ = ["MediaSettingsNormalizer"]

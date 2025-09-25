"""Provide helpers to sanitize history message extras."""

from __future__ import annotations

import logging
from typing import Any, Dict, MutableMapping, Optional, Protocol

from ...telemetry import LogCode, Telemetry, TelemetryChannel
from ...util.entities import sanitize


MutableExtra = MutableMapping[str, Any]


class ExtraHandler(Protocol):
    """Describe a callable that knows how to filter history extras."""

    def __call__(
        self,
        filtered: MutableExtra,
        key: str,
        value: Any,
        *,
        length: int,
        telemetry: Telemetry | None,
        channel: TelemetryChannel | None,
    ) -> None:
        ...


def cleanse(
    extra: Any,
    *,
    length: int,
    telemetry: Telemetry | None = None,
) -> Optional[Dict[str, Any]]:
    """Return sanitized metadata extracted from a history extra mapping."""

    if not isinstance(extra, dict):
        return None

    filtered: Dict[str, Any] = {}
    channel = _derive_channel(telemetry)

    for key, value in extra.items():
        _EXTRA_HANDLERS.get(key, _keep_unknown)(
            filtered, key, value, length=length, telemetry=telemetry, channel=channel
        )

    return filtered or None


def _derive_channel(telemetry: Telemetry | None) -> TelemetryChannel | None:
    """Return a telemetry channel dedicated to this module, if any."""

    return telemetry.channel(__name__) if telemetry else None


def _keep_unknown(
    filtered: MutableExtra,
    key: str,
    value: Any,
    *,
    length: int,
    telemetry: Telemetry | None,
    channel: TelemetryChannel | None,
) -> None:
    """Propagate an unrecognised extra value without modification."""

    del length, telemetry, channel
    filtered[key] = value


def _handle_entities(
    filtered: MutableExtra,
    key: str,
    value: Any,
    *,
    length: int,
    telemetry: Telemetry | None,
    channel: TelemetryChannel | None,
) -> None:
    """Sanitize text entities, emitting telemetry when they are discarded."""

    sanitized = sanitize(value, length, telemetry=telemetry)
    if sanitized:
        filtered[key] = sanitized
    elif channel:
        channel.emit(
            logging.DEBUG,
            LogCode.EXTRA_UNKNOWN_DROPPED,
            filtered_keys=[key],
        )


def _handle_thumb(
    filtered: MutableExtra,
    key: str,
    value: Any,
    *,
    length: int,
    telemetry: Telemetry | None,
    channel: TelemetryChannel | None,
) -> None:
    """Record the presence of a thumbnail without persisting raw data."""

    del length, telemetry, channel
    if value is not None:
        filtered["has_thumb"] = True


_EXTRA_HANDLERS: Dict[str, ExtraHandler] = {
    "entities": _handle_entities,
    "thumb": _handle_thumb,
}


__all__ = ["cleanse"]

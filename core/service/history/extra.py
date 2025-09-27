"""Sanitize and normalize history extra metadata payloads."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Any, Dict, MutableMapping, Optional, Protocol

from ...telemetry import LogCode, Telemetry, TelemetryChannel
from ...util.entities import EntitySanitizer

MutableExtra = MutableMapping[str, Any]


class ExtraHandler(Protocol):
    """Describe a callable that knows how to filter history extras."""

    def __call__(
            self,
            filtered: MutableExtra,
            key: str,
            value: Any,
            context: "ExtraContext",
    ) -> None:
        ...


@dataclass(frozen=True, slots=True)
class ExtraContext:
    """Carry shared parameters for extra sanitization handlers."""

    length: int
    telemetry: Telemetry | None
    channel: TelemetryChannel | None
    entities: EntitySanitizer


def cleanse(
        extra: Any,
        *,
        length: int,
        telemetry: Telemetry | None = None,
        entities: EntitySanitizer,
) -> Optional[Dict[str, Any]]:
    """Return sanitized metadata extracted from a history extra mapping."""

    if not isinstance(extra, dict):
        return None

    filtered: Dict[str, Any] = {}
    channel = _derive_channel(telemetry)
    context = ExtraContext(
        length=length,
        telemetry=telemetry,
        channel=channel,
        entities=entities,
    )

    for key, value in extra.items():
        handler = _EXTRA_HANDLERS.get(key, _keep_unknown)
        handler(filtered, key, value, context)

    return filtered or None


def _derive_channel(telemetry: Telemetry | None) -> TelemetryChannel | None:
    """Return a telemetry channel dedicated to this module, if any."""

    return telemetry.channel(__name__) if telemetry else None


def _keep_unknown(
        filtered: MutableExtra,
        key: str,
        value: Any,
        context: ExtraContext,
) -> None:
    """Propagate an unrecognised extra value without modification."""

    del context
    filtered[key] = value


def _handle_entities(
        filtered: MutableExtra,
        key: str,
        value: Any,
        context: ExtraContext,
) -> None:
    """Sanitize text entities, emitting telemetry when they are discarded."""

    sanitized = context.entities.sanitize(value, context.length)
    if sanitized:
        filtered[key] = sanitized
    elif context.channel:
        context.channel.emit(
            logging.DEBUG,
            LogCode.EXTRA_UNKNOWN_DROPPED,
            filtered_keys=[key],
        )


def _handle_thumb(
        filtered: MutableExtra,
        key: str,
        value: Any,
        context: ExtraContext,
) -> None:
    """Record the presence of a thumbnail without persisting raw data."""

    del context
    if value is not None:
        filtered["has_thumb"] = True


_EXTRA_HANDLERS: Dict[str, ExtraHandler] = {
    "entities": _handle_entities,
    "thumb": _handle_thumb,
}

__all__ = ["cleanse"]

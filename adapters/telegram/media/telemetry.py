"""Telemetry helpers for Telegram media conversions."""

from __future__ import annotations

import logging

from navigator.core.entity.media import MediaItem
from navigator.core.error import NavigatorError
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel


class AlbumTelemetry:
    """Emit telemetry statements related to album conversions."""

    def __init__(self, telemetry: Telemetry | None) -> None:
        self._channel: TelemetryChannel | None = (
            telemetry.channel(__name__) if telemetry else None
        )

    def invalid(self, items: list[MediaItem], *, reason: NavigatorError) -> None:
        if self._channel is None:
            return
        kinds = [getattr(item.type, "value", None) for item in (items or [])]
        self._channel.emit(
            logging.WARNING,
            LogCode.MEDIA_UNSUPPORTED,
            kind="group_invalid",
            types=kinds,
            note=getattr(reason, "code", str(reason)),
        )


__all__ = ["AlbumTelemetry"]

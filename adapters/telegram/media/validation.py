"""Validation helpers for Telegram media processing."""

from __future__ import annotations

from navigator.core.entity.media import MediaItem
from navigator.core.error import NavigatorError
from navigator.core.port.limits import Limits
from navigator.core.service.rendering.album import validate

from .telemetry import AlbumTelemetry


class AlbumValidator:
    """Validate media collections before Telegram assembly."""

    def __init__(self, limits: Limits, telemetry: AlbumTelemetry) -> None:
        self._limits = limits
        self._telemetry = telemetry

    def ensure_valid(self, items: list[MediaItem]) -> None:
        try:
            validate(items, limits=self._limits)
        except NavigatorError as exc:
            self._telemetry.invalid(items, reason=exc)
            raise


__all__ = ["AlbumValidator"]

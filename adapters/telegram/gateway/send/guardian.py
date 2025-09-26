"""Limit enforcement helpers for Telegram send operations."""
from __future__ import annotations

from navigator.core.error import CaptionOverflow, EmptyPayload, TextOverflow
from navigator.core.port.limits import Limits

from .context import SendTelemetry


class LimitsGuardian:
    """Enforce Telegram text and caption limits."""

    def __init__(self, limits: Limits) -> None:
        self._limits = limits

    def caption(
        self,
        caption: str | None,
        truncate: bool,
        reporter: SendTelemetry,
    ) -> str | None:
        if caption is None or len(caption) <= self._limits.captionlimit():
            return caption
        if truncate:
            reporter.truncated("send.caption")
            return caption[: self._limits.captionlimit()]
        raise CaptionOverflow()

    def text(
        self,
        text: str | None,
        truncate: bool,
        reporter: SendTelemetry,
    ) -> str:
        value = text or ""
        if not value.strip():
            raise EmptyPayload()
        if len(value) <= self._limits.textlimit():
            return value
        if not truncate:
            raise TextOverflow()
        reporter.truncated("send.text")
        return value[: self._limits.textlimit()]


__all__ = ["LimitsGuardian"]

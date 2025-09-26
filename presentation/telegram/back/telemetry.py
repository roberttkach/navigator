"""Telemetry helpers for telegram retreat orchestration."""

from __future__ import annotations

import logging

from aiogram.types import CallbackQuery

from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel


class RetreatTelemetry:
    """Isolate telemetry emission for retreat lifecycle events."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    def scope(self, cb: CallbackQuery) -> dict[str, object]:
        return {
            "chat": cb.message.chat.id if cb.message else 0,
            "inline": bool(cb.inline_message_id),
        }

    def entered(self, scope: dict[str, object]) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.ROUTER_BACK_ENTER,
            kind="callback",
            scope=scope,
        )

    def completed(self, scope: dict[str, object]) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.ROUTER_BACK_DONE,
            kind="callback",
            scope=scope,
        )

    def failed(self, note: str, scope: dict[str, object]) -> None:
        self._channel.emit(
            logging.WARNING,
            LogCode.ROUTER_BACK_FAIL,
            kind="callback",
            note=note,
            scope=scope,
        )


__all__ = ["RetreatTelemetry"]

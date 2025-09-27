"""Notification helpers for the Telegram gateway."""
from __future__ import annotations

import logging

from aiogram import Bot

from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope

from .targeting import resolve_targets


class TelegramNotifier:
    """Emit notifications to Telegram chats and record telemetry."""

    def __init__(self, bot: Bot, *, telemetry: Telemetry) -> None:
        self._bot = bot
        self._channel = telemetry.channel(__name__)

    async def alert(self, scope: Scope, text: str) -> None:
        if scope.inline or not text:
            return
        kwargs = resolve_targets(scope)
        await self._bot.send_message(text=text, **kwargs)
        self._channel.emit(
            logging.INFO,
            LogCode.GATEWAY_NOTIFY_OK,
            scope=scope.inline,
            text=len(text),
        )


__all__ = ["TelegramNotifier"]

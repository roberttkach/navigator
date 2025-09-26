"""Deletion helpers for the Telegram gateway."""
from __future__ import annotations

from aiogram import Bot

from navigator.core.telemetry import Telemetry
from navigator.core.value.message import Scope

from .purge import PurgeTask


class TelegramDeletionManager:
    """Coordinate message purge operations for Telegram gateway."""

    def __init__(self, bot: Bot, *, chunk: int, delay: float, telemetry: Telemetry) -> None:
        self._task = PurgeTask(bot, chunk=chunk, delay=delay, telemetry=telemetry)

    async def delete(self, scope: Scope, identifiers: list[int]) -> None:
        await self._task.execute(scope, identifiers)


__all__ = ["TelegramDeletionManager"]

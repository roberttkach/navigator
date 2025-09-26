"""Reply markup helpers for the Telegram gateway."""
from __future__ import annotations

from aiogram import Bot

from navigator.core.port.markup import MarkupCodec
from navigator.core.port.message import Result
from navigator.core.telemetry import Telemetry, TelemetryChannel
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .edit import remap
from .editor import _message_result


class TelegramMarkupRefiner:
    """Manage reply markup remapping for Telegram messages."""

    def __init__(self, bot: Bot, *, codec: MarkupCodec, telemetry: Telemetry) -> None:
        self._bot = bot
        self._codec = codec
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def remap(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        outcome = await remap(
            self._bot,
            codec=self._codec,
            scope=scope,
            identifier=identifier,
            payload=payload,
            channel=self._channel,
        )
        return _message_result(outcome, identifier, payload, scope)


__all__ = ["TelegramMarkupRefiner"]

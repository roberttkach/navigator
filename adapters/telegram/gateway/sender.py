"""Message sending helpers for the Telegram gateway."""
from __future__ import annotations

from aiogram import Bot

from navigator.core.port.limits import Limits
from navigator.core.port.markup import MarkupCodec
from navigator.core.port.message import Result
from navigator.core.port.extraschema import ExtraSchema
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.port.preview import LinkPreviewCodec
from navigator.core.telemetry import Telemetry
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .send import SendRequest, SendSetup, TelegramSendWorkflow
from ..serializer.screen import SignatureScreen


class TelegramMessageSender:
    """Coordinate Telegram send operations for navigator payloads."""

    def __init__(
        self,
        bot: Bot,
        *,
        codec: MarkupCodec,
        limits: Limits,
        schema: ExtraSchema,
        policy: MediaPathPolicy,
        screen: SignatureScreen,
        preview: LinkPreviewCodec | None,
        truncate: bool,
        telemetry: Telemetry,
    ) -> None:
        setup = SendSetup(
            codec=codec,
            schema=schema,
            screen=screen,
            policy=policy,
            limits=limits,
            preview=preview,
        )
        self._workflow = TelegramSendWorkflow(setup=setup, telemetry=telemetry)
        self._bot = bot
        self._truncate = truncate

    async def send(self, scope: Scope, payload: Payload) -> Result:
        request = SendRequest(scope=scope, payload=payload, truncate=self._truncate)
        message, extras, meta = await self._workflow.dispatch(self._bot, request)
        return Result(id=message.message_id, extra=extras, meta=meta)


__all__ = ["TelegramMessageSender"]

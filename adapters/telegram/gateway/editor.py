"""Edit helpers for the Telegram gateway."""
from __future__ import annotations

from aiogram import Bot

from navigator.core.port.extraschema import ExtraSchema
from navigator.core.port.limits import Limits
from navigator.core.port.markup import MarkupCodec
from navigator.core.port.message import Result
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.port.preview import LinkPreviewCodec
from navigator.core.telemetry import Telemetry, TelemetryChannel
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from . import util
from .edit import recast, retitle, rewrite
from ..serializer.screen import SignatureScreen


def _message_result(outcome: object, identifier: int, payload: Payload, scope: Scope) -> Result:
    meta = util.extract(outcome, payload, scope)
    result_id = getattr(outcome, "message_id", identifier)
    return Result(id=result_id, extra=[], meta=meta)


class TelegramMessageEditor:
    """Handle Telegram edit operations using dedicated helpers."""

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
        self._bot = bot
        self._codec = codec
        self._limits = limits
        self._schema = schema
        self._policy = policy
        self._screen = screen
        self._preview = preview
        self._truncate = truncate
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def rewrite(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        outcome = await rewrite(
            self._bot,
            codec=self._codec,
            schema=self._schema,
            screen=self._screen,
            limits=self._limits,
            preview=self._preview,
            scope=scope,
            identifier=identifier,
            payload=payload,
            truncate=self._truncate,
            channel=self._channel,
        )
        return _message_result(outcome, identifier, payload, scope)

    async def recast(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        outcome = await recast(
            self._bot,
            codec=self._codec,
            schema=self._schema,
            screen=self._screen,
            policy=self._policy,
            limits=self._limits,
            scope=scope,
            identifier=identifier,
            payload=payload,
            truncate=self._truncate,
            channel=self._channel,
        )
        return _message_result(outcome, identifier, payload, scope)

    async def retitle(self, scope: Scope, identifier: int, payload: Payload) -> Result:
        outcome = await retitle(
            self._bot,
            codec=self._codec,
            schema=self._schema,
            screen=self._screen,
            limits=self._limits,
            scope=scope,
            identifier=identifier,
            payload=payload,
            truncate=self._truncate,
            channel=self._channel,
        )
        return _message_result(outcome, identifier, payload, scope)

__all__ = ["TelegramMessageEditor", "_message_result"]

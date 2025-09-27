"""Composable helpers orchestrating Telegram send operations."""
from __future__ import annotations

from dataclasses import dataclass

from aiogram import Bot
from aiogram.types import Message

from navigator.core.port.extraschema import ExtraSchema
from navigator.core.port.markup import MarkupCodec
from navigator.core.port.pathpolicy import MediaPathPolicy
from navigator.core.port.preview import LinkPreviewCodec
from navigator.core.port.limits import Limits
from navigator.core.telemetry import Telemetry, TelemetryChannel
from navigator.core.typing.result import Meta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ..serializer.screen import SignatureScreen

from .context import SendContextFactory
from .dependencies import SendDependencies
from .dispatcher import SendDispatcher
from .factory import SendDispatcherFactory


@dataclass(frozen=True)
class SendSetup:
    """Group static dependencies required to dispatch Telegram messages."""

    codec: MarkupCodec
    schema: ExtraSchema
    screen: SignatureScreen
    policy: MediaPathPolicy
    limits: Limits
    preview: LinkPreviewCodec | None = None


@dataclass(frozen=True)
class SendRequest:
    """Dynamic inputs supplied when dispatching a Telegram message."""

    scope: Scope
    payload: Payload
    truncate: bool


class TelegramSendWorkflow:
    """Coordinate Telegram send orchestration behind a stable interface."""

    def __init__(self, *, setup: SendSetup, telemetry: Telemetry) -> None:
        self._dependencies = SendDependencies(
            schema=setup.schema,
            screen=setup.screen,
            policy=setup.policy,
            limits=setup.limits,
            telemetry=telemetry,
        )
        self._dispatcher_factory = SendDispatcherFactory(self._dependencies)
        self._context_factory = SendContextFactory(
            codec=setup.codec,
            preview=setup.preview,
        )
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    def create_dispatcher(self, bot: Bot) -> SendDispatcher:
        """Return a dispatcher bound to the provided ``bot`` instance."""

        return self._dispatcher_factory.create(bot)

    def build_context(self, request: SendRequest) -> object:
        """Build the rendering context consumed by the dispatcher."""

        return self._context_factory.build(
            scope=request.scope,
            payload=request.payload,
            channel=self._channel,
        )

    async def dispatch(
        self,
        bot: Bot,
        request: SendRequest,
    ) -> tuple[Message, list[int], Meta]:
        """Send the provided ``request`` using ``bot`` telemetry wiring."""

        dispatcher = self.create_dispatcher(bot)
        context = self.build_context(request)
        return await dispatcher.dispatch(
            request.payload,
            scope=request.scope,
            context=context,
            truncate=request.truncate,
        )


async def send(
    workflow: TelegramSendWorkflow,
    bot: Bot,
    request: SendRequest,
) -> tuple[Message, list[int], Meta]:
    """Compatibility helper delegating to :class:`TelegramSendWorkflow`."""

    return await workflow.dispatch(bot, request)


__all__ = [
    "SendContextFactory",
    "SendDependencies",
    "SendDispatcher",
    "SendDispatcherFactory",
    "SendRequest",
    "SendSetup",
    "TelegramSendWorkflow",
    "send",
]

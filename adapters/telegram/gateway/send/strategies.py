"""Concrete send strategies for Telegram payload types."""
from __future__ import annotations

from collections.abc import Awaitable, Callable, Iterable, Mapping
from dataclasses import dataclass

from aiogram import Bot
from aiogram.types import Message
from navigator.core.typing.result import GroupMeta, Meta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ..media import assemble
from ..serializer import caption as captionkit
from ..meta import extract_meta

from .context import SendContext
from .dependencies import SendDependencies
from .guardian import LimitsGuardian
from .clusters import GroupClusterBuilder


class AlbumExtrasBuilder:
    """Prepare caption metadata and auxiliary extras for albums."""

    def __init__(self, dependencies: SendDependencies) -> None:
        self._schema = dependencies.schema
        self._screen = dependencies.screen

    def build(
        self,
        bot: Bot,
        *,
        scope: Scope,
        payload: Payload,
    ) -> tuple[Mapping[str, Mapping[str, object]], Mapping[str, object]]:
        caption = captionkit.caption(payload)
        extras = self._schema.send(
            scope,
            payload.extra,
            span=len(caption or ""),
            media=True,
        )
        effect = extras.get("effect")
        addition: Mapping[str, object]
        if effect is None:
            addition = {}
        else:
            addition = self._screen.filter(
                bot.send_media_group,
                {"message_effect_id": effect},
            )
        return extras, addition


class AlbumBundleBuilder:
    """Assemble Telegram media bundles using configured dependencies."""

    def __init__(self, dependencies: SendDependencies) -> None:
        self._policy = dependencies.policy
        self._screen = dependencies.screen
        self._limits = dependencies.limits
        self._telemetry = dependencies.telemetry

    def build(
        self,
        group: Iterable[object],
        *,
        extras: Mapping[str, Mapping[str, object]],
    ) -> Iterable[object]:
        return assemble(
            group,
            captionmeta=extras.get("caption", {}),
            mediameta=extras.get("media", {}),
            policy=self._policy,
            screen=self._screen,
            limits=self._limits,
            native=True,
            telemetry=self._telemetry,
        )


@dataclass(frozen=True)
class AlbumDispatchEnvelope:
    """Describe the plan required to dispatch a media group."""

    bundle: Iterable[object]
    addition: Mapping[str, object]


class AlbumSendPreparation:
    """Produce dispatch envelopes using configured builders."""

    def __init__(self, dependencies: SendDependencies) -> None:
        self._extras = AlbumExtrasBuilder(dependencies)
        self._bundles = AlbumBundleBuilder(dependencies)

    def plan(
        self,
        bot: Bot,
        *,
        scope: Scope,
        payload: Payload,
    ) -> AlbumDispatchEnvelope:
        extras, addition = self._extras.build(bot, scope=scope, payload=payload)
        bundle = self._bundles.build(payload.group, extras=extras)
        return AlbumDispatchEnvelope(bundle=bundle, addition=addition)


class AlbumSendFinalizer:
    """Transform Telegram responses into navigator metadata."""

    def __init__(self) -> None:
        self._clusters = GroupClusterBuilder()

    def finalize(
        self,
        messages: list[Message],
        *,
        payload: Payload,
        scope: Scope,
        reporter: "SendTelemetry",
    ) -> tuple[Message, list[int], GroupMeta]:
        head = messages[0]
        reporter.success(head.message_id, len(messages) - 1)
        meta = GroupMeta(
            clusters=self._clusters.build(messages, payload),
            inline=scope.inline,
        )
        extras_ids = [message.message_id for message in messages[1:]]
        return head, extras_ids, meta


class AlbumSender:
    """Send album payloads via Telegram bot API."""

    def __init__(self, dependencies: SendDependencies) -> None:
        self._preparation = AlbumSendPreparation(dependencies)
        self._finalizer = AlbumSendFinalizer()

    async def send(
        self,
        bot: Bot,
        payload: Payload,
        *,
        scope: Scope,
        context: SendContext,
    ) -> tuple[Message, list[int], GroupMeta]:
        envelope = self._preparation.plan(bot, scope=scope, payload=payload)
        messages = await self._dispatch(bot, envelope, context)
        return self._finalizer.finalize(
            messages,
            payload=payload,
            scope=scope,
            reporter=context.reporter,
        )

    async def _dispatch(
        self,
        bot: Bot,
        envelope: AlbumDispatchEnvelope,
        context: SendContext,
    ) -> list[Message]:
        messages = await bot.send_media_group(
            media=envelope.bundle,
            **context.targets,
            **envelope.addition,
        )
        return list(messages)


@dataclass(frozen=True)
class SingleMediaDispatchPlan:
    """Instruction set required to deliver a single media payload."""

    sender: Callable[..., Awaitable[Message]]
    arguments: dict[str, object]


class SingleMediaPreparation:
    """Derive sender callable and arguments for media payloads."""

    def __init__(self, dependencies: SendDependencies, guard: LimitsGuardian) -> None:
        self._schema = dependencies.schema
        self._screen = dependencies.screen
        self._policy = dependencies.policy
        self._guard = guard

    def plan(
        self,
        bot: Bot,
        payload: Payload,
        *,
        scope: Scope,
        context: SendContext,
        truncate: bool,
    ) -> SingleMediaDispatchPlan:
        caption = captionkit.caption(payload)
        caption = self._guard.caption(caption, truncate, context.reporter)
        extras = self._schema.send(scope, payload.extra, span=len(caption or ""), media=True)
        sender = getattr(bot, f"send_{payload.media.type.value}")
        arguments: dict[str, object] = {
            **context.targets,
            payload.media.type.value: self._policy.adapt(payload.media.path, native=True),
            "reply_markup": context.markup,
        }
        if caption is not None:
            arguments["caption"] = caption
        arguments.update(self._screen.filter(sender, extras.get("caption", {})))
        arguments.update(self._screen.filter(sender, extras.get("media", {})))
        return SingleMediaDispatchPlan(sender=sender, arguments=arguments)


class SingleMediaFinalizer:
    """Create navigator metadata from Telegram media responses."""

    def finalize(
        self,
        message: Message,
        *,
        payload: Payload,
        scope: Scope,
        reporter: "SendTelemetry",
    ) -> tuple[Message, list[int], Meta]:
        reporter.success(message.message_id, 0)
        meta = extract_meta(message, payload, scope)
        return message, [], meta


class SingleMediaSender:
    """Send single media payloads."""

    def __init__(self, dependencies: SendDependencies, guard: LimitsGuardian) -> None:
        self._preparation = SingleMediaPreparation(dependencies, guard)
        self._finalizer = SingleMediaFinalizer()

    async def send(
        self,
        bot: Bot,
        payload: Payload,
        *,
        scope: Scope,
        context: SendContext,
        truncate: bool,
    ) -> tuple[Message, list[int], Meta]:
        plan = self._preparation.plan(
            bot,
            payload,
            scope=scope,
            context=context,
            truncate=truncate,
        )
        message = await plan.sender(**plan.arguments)
        return self._finalizer.finalize(
            message,
            payload=payload,
            scope=scope,
            reporter=context.reporter,
        )


@dataclass(frozen=True)
class TextDispatchPlan:
    """Capture prepared text payload data for dispatch."""

    text: str
    extras: Mapping[str, object]


class TextMessagePreparation:
    """Build text payload dispatch plans using configured dependencies."""

    def __init__(self, dependencies: SendDependencies, guard: LimitsGuardian) -> None:
        self._schema = dependencies.schema
        self._screen = dependencies.screen
        self._guard = guard

    def plan(
        self,
        scope: Scope,
        payload: Payload,
        *,
        truncate: bool,
        reporter: "SendTelemetry",
    ) -> TextDispatchPlan:
        text = self._guard.text(payload.text, truncate, reporter)
        extras = self._schema.send(scope, payload.extra, span=len(text), media=False)
        return TextDispatchPlan(text=text, extras=extras)


class TextMessageFinalizer:
    """Convert Telegram responses for text payloads to navigator meta."""

    def finalize(
        self,
        message: Message,
        *,
        payload: Payload,
        scope: Scope,
        reporter: "SendTelemetry",
    ) -> tuple[Message, list[int], Meta]:
        reporter.success(message.message_id, 0)
        meta = extract_meta(message, payload, scope)
        return message, [], meta


class TextSender:
    """Send plain text payloads."""

    def __init__(self, dependencies: SendDependencies, guard: LimitsGuardian) -> None:
        self._screen = dependencies.screen
        self._preparation = TextMessagePreparation(dependencies, guard)
        self._finalizer = TextMessageFinalizer()

    async def send(
        self,
        bot: Bot,
        payload: Payload,
        *,
        scope: Scope,
        context: SendContext,
        truncate: bool,
    ) -> tuple[Message, list[int], Meta]:
        plan = self._preparation.plan(
            scope,
            payload,
            truncate=truncate,
            reporter=context.reporter,
        )
        message = await self._dispatch(bot, context, plan)
        return self._finalizer.finalize(
            message,
            payload=payload,
            scope=scope,
            reporter=context.reporter,
        )

    async def _dispatch(
        self,
        bot: Bot,
        context: SendContext,
        plan: TextDispatchPlan,
    ) -> Message:
        return await bot.send_message(
            **context.targets,
            text=plan.text,
            reply_markup=context.markup,
            link_preview_options=context.preview,
            **self._screen.filter(bot.send_message, plan.extras.get("text", {})),
        )


__all__ = ["AlbumSender", "SingleMediaSender", "TextSender"]

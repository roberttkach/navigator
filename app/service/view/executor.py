"""Drive Telegram edits according to reconciliation verdicts."""

from __future__ import annotations

import logging
from collections.abc import Awaitable, Callable
from dataclasses import dataclass, replace
from navigator.core.entity.history import Entry, Message
from navigator.core.error import (
    CaptionOverflow,
    EditForbidden,
    EmptyPayload,
    ExtraForbidden,
    MetadataKindMissing,
    MessageUnchanged,
    TextOverflow,
)
from navigator.core.port.message import MessageGateway, Result
from navigator.core.service.rendering import decision
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.typing.result import GroupMeta, MediaMeta, Meta, TextMeta
from navigator.core.value.content import Payload, caption
from navigator.core.value.message import Scope
from typing import Optional


def _head(entity: Entry | Message | None) -> Optional[Message]:
    """Return the most recent message associated with ``entity``."""

    if entity is None:
        return None
    if isinstance(entity, Message):
        return entity
    if getattr(entity, "messages", None):
        try:
            return entity.messages[0]
        except Exception:  # pragma: no cover - defensive
            return None
    return None


def _targets(message: Message | None) -> list[int]:
    """Collect identifiers that need deletion after resend fallbacks."""

    if not message:
        return []
    bundle = [int(message.id)]
    bundle.extend(int(x) for x in (message.extras or []))
    return bundle


@dataclass(slots=True)
class Execution:
    """Capture the gateway response alongside the stem message."""

    result: Result
    stem: Message | None


class FallbackStrategy:
    """Coordinate fallback resend operations when edits are forbidden."""

    def __init__(self, gateway: MessageGateway) -> None:
        self._gateway = gateway

    async def resend(
        self,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Execution:
        result = await self._gateway.send(scope, payload)
        if stem:
            await self._gateway.delete(scope, _targets(stem))
        return Execution(result=result, stem=stem)


class VerdictDispatcher:
    """Dispatch reconciliation decisions to the Telegram gateway."""

    _Handler = Callable[[Scope, Payload, Message | None], Awaitable[Optional[Execution]]]

    def __init__(
        self,
        gateway: MessageGateway,
        *,
        fallback: FallbackStrategy | None = None,
    ) -> None:
        self._gateway = gateway
        self._fallback = fallback or FallbackStrategy(gateway)
        self._handlers: dict[decision.Decision, VerdictDispatcher._Handler] = {
            decision.Decision.RESEND: self._send,
            decision.Decision.EDIT_TEXT: self._rewrite,
            decision.Decision.EDIT_MEDIA: self._recast,
            decision.Decision.EDIT_MEDIA_CAPTION: self._retitle,
            decision.Decision.EDIT_MARKUP: self._remap,
            decision.Decision.DELETE_SEND: self._delete_and_send,
        }

    async def dispatch(
        self,
        verdict: decision.Decision,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Optional[Execution]:
        handler = self._handlers.get(verdict)
        if handler is None:
            return None
        return await handler(scope, payload, stem)

    async def _send(self, scope: Scope, payload: Payload, stem: Message | None) -> Execution:
        result = await self._gateway.send(scope, payload)
        return Execution(result=result, stem=stem)

    async def _rewrite(
        self,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Optional[Execution]:
        if not stem:
            return None
        result = await self._gateway.rewrite(scope, stem.id, payload)
        return Execution(result=result, stem=stem)

    async def _recast(
        self,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Optional[Execution]:
        if not stem:
            return None
        result = await self._gateway.recast(scope, stem.id, payload)
        return Execution(result=result, stem=stem)

    async def _retitle(
        self,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Optional[Execution]:
        if not stem:
            return None
        result = await self._gateway.retitle(scope, stem.id, payload)
        return Execution(result=result, stem=stem)

    async def _remap(
        self,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Optional[Execution]:
        if not stem:
            return None
        result = await self._gateway.remap(scope, stem.id, payload)
        return Execution(result=result, stem=stem)

    async def _delete_and_send(
        self,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Execution:
        return await self._fallback.resend(scope, payload, stem)


class EditTelemetry:
    """Emit telemetry statements for edit execution."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    def skip(self, note: str) -> None:
        self._channel.emit(logging.INFO, LogCode.RERENDER_START, note=note, skip=True)

    def event(self, note: str) -> None:
        self._channel.emit(logging.INFO, LogCode.RERENDER_START, note=note)

    def inline_blocked(self, scope: Scope, note: str) -> None:
        if scope.inline:
            self._channel.emit(
                logging.INFO,
                LogCode.RERENDER_INLINE_NO_FALLBACK,
                note=note,
                skip=True,
            )


class EditErrorHandler:
    """Translate gateway failures into telemetry and fallbacks."""

    def __init__(
        self,
        telemetry: EditTelemetry,
        fallback: FallbackStrategy,
    ) -> None:
        self._telemetry = telemetry
        self._fallback = fallback

    async def resolve(
        self,
        error: Exception,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Optional[Execution]:
        if isinstance(error, EmptyPayload):
            self._telemetry.skip("empty_payload")
            return None
        if isinstance(error, ExtraForbidden):
            self._telemetry.skip("extra_validation_failed")
            return None
        if isinstance(error, (TextOverflow, CaptionOverflow)):
            self._telemetry.skip("too_long")
            return None
        if isinstance(error, EditForbidden):
            self._telemetry.event("edit_forbidden")
            self._telemetry.inline_blocked(scope, "inline_no_fallback")
            if scope.inline:
                return None
            return await self._fallback.resend(scope, payload, stem)
        if isinstance(error, MessageUnchanged):
            self._telemetry.event("not_modified")
            self._telemetry.inline_blocked(scope, "inline_no_fallback")
            if scope.inline:
                return None
            return None
        raise error


class MetaRefiner:
    """Reconcile execution metadata with persisted message state."""

    def refine(
        self,
        execution: Execution,
        verdict: decision.Decision,
        payload: Payload,
    ) -> Meta:
        _ = verdict
        meta = execution.result.meta
        stem = execution.stem

        if isinstance(meta, MediaMeta):
            medium = meta.medium
            if medium is None and stem and stem.media:
                medium = getattr(stem.media.type, "value", None)

            file = meta.file
            if file is None:
                path = getattr(getattr(payload, "media", None), "path", None)
                if isinstance(path, str):
                    file = path
                elif stem and stem.media and isinstance(getattr(stem.media, "path", None), str):
                    file = stem.media.path

            captioncopy = meta.caption
            if captioncopy is None:
                fresh = caption(payload)
                if fresh is not None:
                    captioncopy = fresh
                elif getattr(payload, "erase", False):
                    captioncopy = ""
                elif stem and stem.media:
                    captioncopy = stem.media.caption

            return replace(meta, medium=medium, file=file, caption=captioncopy)

        if isinstance(meta, TextMeta) and stem and stem.text is not None:
            textcopy = meta.text if meta.text is not None else stem.text
            return replace(meta, text=textcopy)

        if isinstance(meta, (GroupMeta, TextMeta, MediaMeta)):
            return meta

        raise MetadataKindMissing()


class EditCleanup:
    """Encapsulate deletion routines executed after edit operations."""

    def __init__(self, gateway: MessageGateway) -> None:
        self._gateway = gateway

    async def delete(self, scope: Scope, identifiers: list[int]) -> None:
        if identifiers:
            await self._gateway.delete(scope, identifiers)


@dataclass(slots=True)
class EditComponents:
    """Aggregate edit collaborators to reduce executor responsibilities."""

    dispatcher: VerdictDispatcher
    errors: EditErrorHandler
    refiner: MetaRefiner
    cleanup: EditCleanup


class EditExecutor:
    """Dispatch reconciliation decisions to the Telegram gateway."""

    def __init__(
        self,
        gateway: MessageGateway,
        telemetry: Telemetry,
        *,
        dispatcher: VerdictDispatcher | None = None,
        errors: EditErrorHandler | None = None,
        refiner: MetaRefiner | None = None,
        cleanup: EditCleanup | None = None,
    ) -> None:
        fallback = FallbackStrategy(gateway)
        telemetry_helper = EditTelemetry(telemetry)
        self._components = EditComponents(
            dispatcher=dispatcher or VerdictDispatcher(gateway, fallback=fallback),
            errors=errors or EditErrorHandler(telemetry_helper, fallback),
            refiner=refiner or MetaRefiner(),
            cleanup=cleanup or EditCleanup(gateway),
        )

    async def execute(
            self,
            scope: Scope,
            verdict: decision.Decision,
            payload: Payload,
            last: Entry | Message | None,
    ) -> Optional[Execution]:
        """Apply ``verdict`` using the gateway and return execution metadata."""

        stem = _head(last)

        try:
            if verdict is decision.Decision.NO_CHANGE:
                return None

            return await self._components.dispatcher.dispatch(verdict, scope, payload, stem)

        except (
            EmptyPayload,
            ExtraForbidden,
            TextOverflow,
            CaptionOverflow,
            EditForbidden,
            MessageUnchanged,
        ) as error:
            return await self._components.errors.resolve(error, scope, payload, stem)

    async def delete(self, scope: Scope, identifiers: list[int]) -> None:
        await self._components.cleanup.delete(scope, identifiers)

    def refine(
            self,
            execution: Execution,
            verdict: decision.Decision,
            payload: Payload,
    ) -> Meta:
        """Reconcile execution metadata with persisted message state."""

        return self._components.refiner.refine(execution, verdict, payload)


__all__ = ["EditExecutor", "Execution"]

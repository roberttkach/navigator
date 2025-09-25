"""Coordinate Telegram edit operations based on reconciliation verdicts."""

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


class EditExecutor:
    """Dispatch reconciliation decisions to the Telegram gateway."""

    _Handler = Callable[[Scope, Payload, Message | None], Awaitable[Optional[Execution]]]

    def __init__(self, gateway: MessageGateway, telemetry: Telemetry) -> None:
        self._gateway = gateway
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._handlers: dict[decision.Decision, EditExecutor._Handler] = {
            decision.Decision.RESEND: self._send,
            decision.Decision.EDIT_TEXT: self._rewrite,
            decision.Decision.EDIT_MEDIA: self._recast,
            decision.Decision.EDIT_MEDIA_CAPTION: self._retitle,
            decision.Decision.EDIT_MARKUP: self._remap,
            decision.Decision.DELETE_SEND: self._delete_and_send,
        }

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

            handler = self._handlers.get(verdict)
            if handler is None:
                return None

            return await handler(scope, payload, stem)

        except EmptyPayload:
            self._channel.emit(
                logging.INFO,
                LogCode.RERENDER_START,
                note="empty_payload",
                skip=True,
            )
            return None
        except ExtraForbidden:
            self._channel.emit(
                logging.INFO,
                LogCode.RERENDER_START,
                note="extra_validation_failed",
                skip=True,
            )
            return None
        except (TextOverflow, CaptionOverflow):
            self._channel.emit(
                logging.INFO,
                LogCode.RERENDER_START,
                note="too_long",
                skip=True,
            )
            return None
        except EditForbidden:
            self._channel.emit(logging.INFO, LogCode.RERENDER_START, note="edit_forbidden")
            if scope.inline:
                self._channel.emit(
                    logging.INFO,
                    LogCode.RERENDER_INLINE_NO_FALLBACK,
                    note="inline_no_fallback",
                    skip=True,
                )
                return None
            result = await self._gateway.send(scope, payload)
            if stem:
                await self._gateway.delete(scope, _targets(stem))
            return Execution(result=result, stem=stem)
        except MessageUnchanged:
            self._channel.emit(logging.INFO, LogCode.RERENDER_START, note="not_modified")
            if scope.inline:
                self._channel.emit(
                    logging.INFO,
                    LogCode.RERENDER_INLINE_NO_FALLBACK,
                    note="inline_no_fallback",
                    skip=True,
                )
                return None
            return None

    async def _send(self, scope: Scope, payload: Payload, stem: Message | None) -> Execution:
        result = await self._gateway.send(scope, payload)
        return Execution(result=result, stem=stem)

    async def _rewrite(
            self, scope: Scope, payload: Payload, stem: Message | None
    ) -> Optional[Execution]:
        if not stem:
            return None
        result = await self._gateway.rewrite(scope, stem.id, payload)
        return Execution(result=result, stem=stem)

    async def _recast(
            self, scope: Scope, payload: Payload, stem: Message | None
    ) -> Optional[Execution]:
        if not stem:
            return None
        result = await self._gateway.recast(scope, stem.id, payload)
        return Execution(result=result, stem=stem)

    async def _retitle(
            self, scope: Scope, payload: Payload, stem: Message | None
    ) -> Optional[Execution]:
        if not stem:
            return None
        result = await self._gateway.retitle(scope, stem.id, payload)
        return Execution(result=result, stem=stem)

    async def _remap(
            self, scope: Scope, payload: Payload, stem: Message | None
    ) -> Optional[Execution]:
        if not stem:
            return None
        result = await self._gateway.remap(scope, stem.id, payload)
        return Execution(result=result, stem=stem)

    async def _delete_and_send(
            self, scope: Scope, payload: Payload, stem: Message | None
    ) -> Execution:
        result = await self._gateway.send(scope, payload)
        if stem:
            await self._gateway.delete(scope, _targets(stem))
        return Execution(result=result, stem=stem)

    async def delete(self, scope: Scope, identifiers: list[int]) -> None:
        if identifiers:
            await self._gateway.delete(scope, identifiers)

    def refine(
            self,
            execution: Execution,
            verdict: decision.Decision,
            payload: Payload,
    ) -> Meta:
        """Reconcile execution metadata with persisted message state."""

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


__all__ = ["EditExecutor", "Execution"]

from __future__ import annotations

import logging
from dataclasses import dataclass, replace
from typing import Optional

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

def _head(entity: Entry | Message | None) -> Optional[Message]:
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
    if not message:
        return []
    bundle = [int(message.id)]
    bundle.extend(int(x) for x in (message.extras or []))
    return bundle


@dataclass(slots=True)
class Execution:
    result: Result
    stem: Message | None


class EditExecutor:
    def __init__(self, gateway: MessageGateway, telemetry: Telemetry) -> None:
        self._gateway = gateway
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def execute(
        self,
        scope: Scope,
        verdict: decision.Decision,
        payload: Payload,
        last: Entry | Message | None,
    ) -> Optional[Execution]:
        stem = _head(last)

        try:
            if verdict is decision.Decision.NO_CHANGE:
                return None

            if verdict is decision.Decision.RESEND:
                result = await self._gateway.send(scope, payload)
                return Execution(result=result, stem=stem)

            if verdict is decision.Decision.EDIT_TEXT:
                if not stem:
                    return None
                result = await self._gateway.rewrite(scope, stem.id, payload)
                return Execution(result=result, stem=stem)

            if verdict is decision.Decision.EDIT_MEDIA:
                if not stem:
                    return None
                result = await self._gateway.recast(scope, stem.id, payload)
                return Execution(result=result, stem=stem)

            if verdict is decision.Decision.EDIT_MEDIA_CAPTION:
                if not stem:
                    return None
                result = await self._gateway.retitle(scope, stem.id, payload)
                return Execution(result=result, stem=stem)

            if verdict is decision.Decision.EDIT_MARKUP:
                if not stem:
                    return None
                result = await self._gateway.remap(scope, stem.id, payload)
                return Execution(result=result, stem=stem)

            if verdict is decision.Decision.DELETE_SEND:
                result = await self._gateway.send(scope, payload)
                if stem:
                    await self._gateway.delete(scope, _targets(stem))
                return Execution(result=result, stem=stem)

            return None

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

    async def delete(self, scope: Scope, identifiers: list[int]) -> None:
        if identifiers:
            await self._gateway.delete(scope, identifiers)

    def refine_meta(
        self,
        execution: Execution,
        verdict: decision.Decision,
        payload: Payload,
    ) -> Meta:
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

            caption_value = meta.caption
            if caption_value is None:
                fresh = caption(payload)
                if fresh is not None:
                    caption_value = fresh
                elif getattr(payload, "erase", False):
                    caption_value = ""
                elif stem and stem.media:
                    caption_value = stem.media.caption

            return replace(meta, medium=medium, file=file, caption=caption_value)

        if isinstance(meta, TextMeta) and stem and stem.text is not None:
            text_value = meta.text if meta.text is not None else stem.text
            return replace(meta, text=text_value)

        if isinstance(meta, (GroupMeta, TextMeta, MediaMeta)):
            return meta

        raise MetadataKindMissing()


__all__ = ["EditExecutor", "Execution"]

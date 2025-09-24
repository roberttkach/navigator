from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import Optional

from domain.entity.history import Message, Entry
from domain.error import (
    CaptionOverflow,
    EditForbidden,
    EmptyPayload,
    ExtraForbidden,
    MessageUnchanged,
    TextOverflow,
)
from domain.log.code import LogCode
from domain.log.emit import jlog
from domain.port.message import MessageGateway, Result
from domain.service.rendering import decision
from domain.value.content import Payload, caption
from domain.value.message import Scope

logger = logging.getLogger(__name__)


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
    def __init__(self, gateway: MessageGateway) -> None:
        self._gateway = gateway

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
            jlog(
                logger,
                logging.INFO,
                LogCode.RERENDER_START,
                note="empty_payload",
                skip=True,
            )
            return None
        except ExtraForbidden:
            jlog(
                logger,
                logging.INFO,
                LogCode.RERENDER_START,
                note="extra_validation_failed",
                skip=True,
            )
            return None
        except (TextOverflow, CaptionOverflow):
            jlog(
                logger,
                logging.INFO,
                LogCode.RERENDER_START,
                note="too_long",
                skip=True,
            )
            return None
        except EditForbidden:
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="edit_forbidden")
            if scope.inline:
                jlog(
                    logger,
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
            jlog(logger, logging.INFO, LogCode.RERENDER_START, note="not_modified")
            if scope.inline:
                jlog(
                    logger,
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
    ) -> dict:
        meta = {
            "kind": getattr(execution.result, "kind", None),
            "medium": getattr(execution.result, "medium", None),
            "file": getattr(execution.result, "file", None),
            "caption": getattr(execution.result, "caption", None),
            "text": getattr(execution.result, "text", None),
            "clusters": getattr(execution.result, "clusters", None),
            "inline": getattr(execution.result, "inline", None),
        }

        stem = execution.stem
        if meta.get("kind") == "media" and stem and stem.media:
            if meta.get("medium") is None:
                meta["medium"] = getattr(stem.media.type, "value", None)

            if meta.get("file") is None:
                path = getattr(getattr(payload, "media", None), "path", None)
                if isinstance(path, str):
                    meta["file"] = path
                elif isinstance(getattr(stem.media, "path", None), str):
                    meta["file"] = stem.media.path

            if meta.get("caption") is None:
                fresh = caption(payload)
                if fresh is not None:
                    meta["caption"] = fresh
                elif payload.erase:
                    meta["caption"] = ""
                else:
                    meta["caption"] = stem.media.caption

        if meta.get("kind") == "text" and stem and stem.text is not None:
            if meta.get("text") is None:
                meta["text"] = stem.text

        kind = meta.get("kind")
        if kind not in {"text", "media", "group"}:
            raise ValueError("render_meta_missing_kind")

        return meta


__all__ = ["EditExecutor", "Execution"]

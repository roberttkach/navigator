from __future__ import annotations

import logging

from domain.entity.history import Entry, Message
from domain.entity.media import MediaType
from domain.log.code import LogCode
from domain.log.emit import jlog
from domain.port.pathpolicy import MediaPathPolicy
from domain.service.rendering import decision as _d
from domain.service.rendering.config import RenderingConfig
from domain.service.rendering.helpers import match
from domain.value.content import Payload
from domain.value.message import Scope

from ...internal.rules.inline import remap as remap_decision
from ..store import preserve
from .executor import EditExecutor, Execution

logger = logging.getLogger(__name__)


class InlineOutcome:
    __slots__ = ("execution", "decision", "payload")

    def __init__(self, execution: Execution, decision: _d.Decision, payload: Payload) -> None:
        self.execution = execution
        self.decision = decision
        self.payload = payload


class InlineStrategy:
    def __init__(self, policy: MediaPathPolicy) -> None:
        self._policy = policy
        self._logger = logging.getLogger(__name__)

    def _admissible(self, payload: Payload) -> bool:
        media = getattr(payload, "media", None)
        if not media:
            return False
        if media.type in (MediaType.VOICE, MediaType.VIDEO_NOTE):
            return False
        return self._policy.admissible(media.path, inline=True)

    async def handle(
        self,
        *,
        scope: Scope,
        payload: Payload,
        tail: Message | None,
        executor: EditExecutor,
        config: RenderingConfig,
    ) -> InlineOutcome | None:
        entry = preserve(payload, tail)
        if getattr(entry, "group", None):
            entry = entry.morph(media=entry.group[0], group=None)

        base = tail
        media = getattr(entry, "media", None)

        if media:
            if not self._admissible(entry):
                if base and not match(getattr(base, "markup", None), getattr(entry, "reply", None)):
                    adjusted = entry.morph(media=base.media if base else None, group=None)
                    execution = await executor.execute(
                        scope,
                        _d.Decision.EDIT_MARKUP,
                        adjusted,
                        base,
                    )
                    if execution:
                        return InlineOutcome(execution, _d.Decision.EDIT_MARKUP, adjusted)
                jlog(self._logger, logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
                return None

            anchor = Entry(state=None, view=None, messages=[tail]) if tail else None
            fresh_decision = _d.decide(anchor, entry, config)

            if fresh_decision is _d.Decision.DELETE_SEND:
                remapped = remap_decision(base, entry, inline=True)
                jlog(
                    self._logger,
                    logging.INFO,
                    LogCode.INLINE_REMAP_DELETE_SEND,
                    origin="DELETE_SEND",
                    target=remapped.name,
                )
                if remapped is _d.Decision.EDIT_MARKUP:
                    adjusted = entry.morph(media=base.media if base else None, group=None)
                    execution = await executor.execute(scope, remapped, adjusted, base)
                    if execution:
                        return InlineOutcome(execution, remapped, adjusted)
                    return None
                if remapped in (_d.Decision.EDIT_TEXT, _d.Decision.EDIT_MEDIA):
                    execution = await executor.execute(scope, remapped, entry, base)
                    if execution:
                        return InlineOutcome(execution, remapped, entry)
                jlog(self._logger, logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
                return None

            if fresh_decision is _d.Decision.EDIT_MEDIA_CAPTION:
                execution = await executor.execute(scope, fresh_decision, entry, base)
                if execution:
                    return InlineOutcome(execution, fresh_decision, entry)
                return None

            if fresh_decision is _d.Decision.EDIT_MARKUP:
                execution = await executor.execute(scope, fresh_decision, entry, base)
                if execution:
                    return InlineOutcome(execution, fresh_decision, entry)
                return None

            execution = await executor.execute(scope, _d.Decision.EDIT_MEDIA, entry, base)
            if execution:
                return InlineOutcome(execution, _d.Decision.EDIT_MEDIA, entry)
            return None

        if base and getattr(base, "media", None):
            adjusted = entry.morph(media=base.media, group=None)
            extra = adjusted.extra or {}
            if (
                entry.text is not None
                or extra.get("mode") is not None
                or extra.get("entities") is not None
                or extra.get("show_caption_above_media") is not None
            ):
                execution = await executor.execute(
                    scope,
                    _d.Decision.EDIT_MEDIA_CAPTION,
                    adjusted,
                    base,
                )
                if execution:
                    return InlineOutcome(execution, _d.Decision.EDIT_MEDIA_CAPTION, adjusted)
                return None

            if not match(getattr(base, "markup", None), getattr(entry, "reply", None)):
                execution = await executor.execute(
                    scope,
                    _d.Decision.EDIT_MARKUP,
                    adjusted,
                    base,
                )
                if execution:
                    return InlineOutcome(execution, _d.Decision.EDIT_MARKUP, adjusted)
                return None

            jlog(self._logger, logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
            return None

        execution = await executor.execute(scope, _d.Decision.EDIT_TEXT, entry, base)
        if execution:
            return InlineOutcome(execution, _d.Decision.EDIT_TEXT, entry)
        return None


__all__ = ["InlineStrategy", "InlineOutcome"]

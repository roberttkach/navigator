from __future__ import annotations

import logging
from dataclasses import dataclass

from navigator.core.entity.history import Entry, Message
from navigator.core.service.rendering import decision as D
from navigator.core.service.rendering.config import RenderingConfig
from navigator.core.service.rendering.helpers import match
from navigator.core.telemetry import LogCode, telemetry
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from ..executor import EditExecutor
from ...store import preserve
from .editor import InlineEditor, InlineOutcome
from .guard import InlineGuard
from .remap import InlineRemapper

channel = telemetry.channel(__name__)


@dataclass(slots=True)
class InlineHandler:
    guard: InlineGuard
    remapper: InlineRemapper
    editor: InlineEditor

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
            if not self.guard.admissible(entry):
                return await self._fallback_markup(scope, entry, base, executor)
            anchor = Entry(state=None, view=None, messages=[tail]) if tail else None
            verdict = D.decide(anchor, entry, config)
            return await self._handle_media(scope, verdict, entry, base, executor)

        return await self._handle_text(scope, entry, base, executor)

    async def _handle_media(
        self,
        scope: Scope,
        verdict: D.Decision,
        entry: Payload,
        base: Message | None,
        executor: EditExecutor,
    ) -> InlineOutcome | None:
        if verdict is D.Decision.DELETE_SEND:
            remapped = self.remapper.remap(base, entry)
            channel.emit(
                logging.INFO,
                LogCode.INLINE_REMAP_DELETE_SEND,
                origin="DELETE_SEND",
                target=remapped.name,
            )
            if remapped is D.Decision.EDIT_MARKUP:
                adjusted = entry.morph(media=base.media if base else None, group=None)
                return await self.editor.apply(scope, remapped, adjusted, base, executor=executor)
            if remapped in (D.Decision.EDIT_TEXT, D.Decision.EDIT_MEDIA):
                outcome = await self.editor.apply(scope, remapped, entry, base, executor=executor)
                if outcome:
                    return outcome
            channel.emit(logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
            return None

        if verdict is D.Decision.EDIT_MEDIA_CAPTION:
            return await self.editor.apply(scope, verdict, entry, base, executor=executor)

        if verdict is D.Decision.EDIT_MARKUP:
            return await self.editor.apply(scope, verdict, entry, base, executor=executor)

        return await self.editor.apply(scope, D.Decision.EDIT_MEDIA, entry, base, executor=executor)

    async def _handle_text(
        self,
        scope: Scope,
        entry: Payload,
        base: Message | None,
        executor: EditExecutor,
    ) -> InlineOutcome | None:
        if base and getattr(base, "media", None):
            adjusted = entry.morph(media=base.media, group=None)
            extra = adjusted.extra or {}
            if (
                entry.text is not None
                or extra.get("mode") is not None
                or extra.get("entities") is not None
                or extra.get("show_caption_above_media") is not None
            ):
                return await self.editor.apply(
                    scope,
                    D.Decision.EDIT_MEDIA_CAPTION,
                    adjusted,
                    base,
                    executor=executor,
                )
            if not match(getattr(base, "markup", None), getattr(entry, "reply", None)):
                return await self.editor.apply(
                    scope,
                    D.Decision.EDIT_MARKUP,
                    adjusted,
                    base,
                    executor=executor,
                )
            channel.emit(logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
            return None

        return await self.editor.apply(scope, D.Decision.EDIT_TEXT, entry, base, executor=executor)

    async def _fallback_markup(
        self,
        scope: Scope,
        entry: Payload,
        base: Message | None,
        executor: EditExecutor,
    ) -> InlineOutcome | None:
        if base and not match(getattr(base, "markup", None), getattr(entry, "reply", None)):
            adjusted = entry.morph(media=base.media if base else None, group=None)
            outcome = await self.editor.apply(
                scope,
                D.Decision.EDIT_MARKUP,
                adjusted,
                base,
                executor=executor,
            )
            if outcome:
                return outcome
        channel.emit(logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
        return None


__all__ = ["InlineHandler", "InlineOutcome", "InlineEditor", "InlineGuard", "InlineRemapper"]

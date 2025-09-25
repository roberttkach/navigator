"""Coordinate inline-specific reconciliation between payloads and history."""

from __future__ import annotations

import logging
from dataclasses import dataclass, field
from navigator.core.entity.history import Message
from navigator.core.service.rendering import decision as D
from navigator.core.service.rendering.config import RenderingConfig
from navigator.core.service.rendering.helpers import match
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .editor import InlineEditor, InlineOutcome
from .guard import InlineGuard
from .remap import InlineRemapper
from ..executor import EditExecutor
from ...store import preserve


@dataclass(slots=True)
class InlineHandler:
    """Mediate inline edits, remapping fallbacks when required."""

    guard: InlineGuard
    remapper: InlineRemapper
    editor: InlineEditor
    telemetry: Telemetry
    _channel: TelemetryChannel = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._channel = self.telemetry.channel(__name__)

    async def handle(
            self,
            *,
            scope: Scope,
            payload: Payload,
            tail: Message | None,
            executor: EditExecutor,
            config: RenderingConfig,
    ) -> InlineOutcome | None:
        """Plan inline reconciliation for the provided ``payload``."""

        entry = self._prepare_candidate(payload, tail)
        base = tail
        media = getattr(entry, "media", None)

        if media:
            if not self.guard.admissible(entry):
                return await self._fallback(scope, entry, base, executor)
            verdict = D.decide(tail, entry, config)
            return await self._mediate(scope, verdict, entry, base, executor)

        return await self._scribe(scope, entry, base, executor)

    def _prepare_candidate(self, payload: Payload, tail: Message | None) -> Payload:
        """Derive preserved inline payload ready for inline editing."""

        entry = preserve(payload, tail)
        if getattr(entry, "group", None):
            return entry.morph(media=entry.group[0], group=None)
        return entry

    async def _mediate(
            self,
            scope: Scope,
            verdict: D.Decision,
            entry: Payload,
            base: Message | None,
            executor: EditExecutor,
    ) -> InlineOutcome | None:
        """Apply verdict-specific inline reconciliation logic."""

        if verdict is D.Decision.DELETE_SEND:
            return await self._handle_delete_send(scope, entry, base, executor=executor)

        if verdict in (D.Decision.EDIT_MEDIA_CAPTION, D.Decision.EDIT_MARKUP):
            return await self._apply_edit(scope, verdict, entry, base, executor=executor)

        return await self._apply_edit(
            scope,
            D.Decision.EDIT_MEDIA,
            entry,
            base,
            executor=executor,
        )

    async def _scribe(
            self,
            scope: Scope,
            entry: Payload,
            base: Message | None,
            executor: EditExecutor,
    ) -> InlineOutcome | None:
        """Handle inline updates when the preserved payload is textual."""

        if base and getattr(base, "media", None):
            adjusted = entry.morph(media=base.media, group=None)
            if self._requires_caption_refresh(adjusted):
                return await self._apply_edit(
                    scope,
                    D.Decision.EDIT_MEDIA_CAPTION,
                    adjusted,
                    base,
                    executor=executor,
                )
            if not match(getattr(base, "markup", None), getattr(entry, "reply", None)):
                return await self._apply_edit(
                    scope,
                    D.Decision.EDIT_MARKUP,
                    adjusted,
                    base,
                    executor=executor,
                )
            return self._deny_switch()

        return await self._apply_edit(
            scope,
            D.Decision.EDIT_TEXT,
            entry,
            base,
            executor=executor,
        )

    async def _fallback(
            self,
            scope: Scope,
            entry: Payload,
            base: Message | None,
            executor: EditExecutor,
    ) -> InlineOutcome | None:
        """Attempt graceful inline fallback when guard rejects the payload."""

        if base and not match(getattr(base, "markup", None), getattr(entry, "reply", None)):
            adjusted = entry.morph(media=base.media if base else None, group=None)
            outcome = await self._apply_edit(
                scope,
                D.Decision.EDIT_MARKUP,
                adjusted,
                base,
                executor=executor,
            )
            if outcome:
                return outcome
        return self._deny_switch()

    async def _apply_edit(
            self,
            scope: Scope,
            verdict: D.Decision,
            payload: Payload,
            base: Message | None,
            executor: EditExecutor,
    ) -> InlineOutcome | None:
        """Delegate inline edits to the executor with consistent wiring."""

        return await self.editor.apply(
            scope,
            verdict,
            payload,
            base,
            executor=executor,
        )

    async def _handle_delete_send(
            self,
            scope: Scope,
            entry: Payload,
            base: Message | None,
            executor: EditExecutor,
    ) -> InlineOutcome | None:
        """Resolve delete-send verdicts through inline remapping."""

        remapped = self.remapper.remap(base, entry)
        self._channel.emit(
            logging.INFO,
            LogCode.INLINE_REMAP_DELETE_SEND,
            origin="DELETE_SEND",
            target=remapped.name,
        )
        if remapped is D.Decision.EDIT_MARKUP:
            adjusted = entry.morph(media=base.media if base else None, group=None)
            return await self._apply_edit(
                scope,
                remapped,
                adjusted,
                base,
                executor=executor,
            )
        if remapped in (D.Decision.EDIT_TEXT, D.Decision.EDIT_MEDIA):
            outcome = await self._apply_edit(
                scope,
                remapped,
                entry,
                base,
                executor=executor,
            )
            if outcome:
                return outcome
        return self._deny_switch()

    def _deny_switch(self) -> None:
        """Emit telemetry for forbidden inline content switches."""

        self._channel.emit(logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)
        return None

    def _requires_caption_refresh(self, payload: Payload) -> bool:
        """Report whether inline payload changes caption semantics."""

        extra = payload.extra or {}
        return bool(
            payload.text is not None
            or extra.get("mode") is not None
            or extra.get("entities") is not None
            or extra.get("show_caption_above_media") is not None
        )


__all__ = ["InlineHandler", "InlineOutcome", "InlineEditor", "InlineGuard", "InlineRemapper"]

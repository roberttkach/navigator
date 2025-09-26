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


class InlineTelemetryAdapter:
    """Emit inline-related telemetry events."""

    def __init__(self, telemetry: Telemetry) -> None:
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    def remap_delete_send(self, target: D.Decision) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.INLINE_REMAP_DELETE_SEND,
            origin="DELETE_SEND",
            target=target.name,
        )

    def deny_switch(self) -> None:
        self._channel.emit(logging.INFO, LogCode.INLINE_CONTENT_SWITCH_FORBIDDEN)


class InlineCandidateBuilder:
    """Prepare preserved payloads suitable for inline editing."""

    def create(self, payload: Payload, tail: Message | None) -> Payload:
        entry = preserve(payload, tail)
        if getattr(entry, "group", None):
            return entry.morph(media=entry.group[0], group=None)
        return entry


class InlineEditMediator:
    """Delegate inline edits to the executor with consistent wiring."""

    def __init__(self, editor: InlineEditor) -> None:
        self._editor = editor

    async def apply(
        self,
        scope: Scope,
        verdict: D.Decision,
        payload: Payload,
        base: Message | None,
        *,
        executor: EditExecutor,
    ) -> InlineOutcome | None:
        return await self._editor.apply(
            scope,
            verdict,
            payload,
            base,
            executor=executor,
        )


class InlineMediaFlow:
    """Coordinate inline media decisions and fallbacks."""

    def __init__(
        self,
        guard: InlineGuard,
        remapper: InlineRemapper,
        mediator: InlineEditMediator,
        telemetry: InlineTelemetryAdapter,
    ) -> None:
        self._guard = guard
        self._remapper = remapper
        self._mediator = mediator
        self._telemetry = telemetry

    async def handle(
        self,
        scope: Scope,
        entry: Payload,
        base: Message | None,
        executor: EditExecutor,
        config: RenderingConfig,
    ) -> InlineOutcome | None:
        if not self._guard.admissible(entry):
            return await self._fallback(scope, entry, base, executor)
        verdict = D.decide(base, entry, config)
        return await self._mediate(scope, verdict, entry, base, executor)

    async def _fallback(
        self,
        scope: Scope,
        entry: Payload,
        base: Message | None,
        executor: EditExecutor,
    ) -> InlineOutcome | None:
        if base and not match(getattr(base, "markup", None), getattr(entry, "reply", None)):
            adjusted = entry.morph(media=base.media if base else None, group=None)
            outcome = await self._mediator.apply(
                scope,
                D.Decision.EDIT_MARKUP,
                adjusted,
                base,
                executor=executor,
            )
            if outcome:
                return outcome
        self._telemetry.deny_switch()
        return None

    async def _mediate(
        self,
        scope: Scope,
        verdict: D.Decision,
        entry: Payload,
        base: Message | None,
        executor: EditExecutor,
    ) -> InlineOutcome | None:
        if verdict is D.Decision.DELETE_SEND:
            return await self._handle_delete_send(scope, entry, base, executor=executor)
        if verdict in (D.Decision.EDIT_MEDIA_CAPTION, D.Decision.EDIT_MARKUP):
            return await self._mediator.apply(
                scope,
                verdict,
                entry,
                base,
                executor=executor,
            )
        return await self._mediator.apply(
            scope,
            D.Decision.EDIT_MEDIA,
            entry,
            base,
            executor=executor,
        )

    async def _handle_delete_send(
        self,
        scope: Scope,
        entry: Payload,
        base: Message | None,
        *,
        executor: EditExecutor,
    ) -> InlineOutcome | None:
        remapped = self._remapper.remap(base, entry)
        self._telemetry.remap_delete_send(remapped)
        if remapped is D.Decision.EDIT_MARKUP:
            adjusted = entry.morph(media=base.media if base else None, group=None)
            return await self._mediator.apply(
                scope,
                remapped,
                adjusted,
                base,
                executor=executor,
            )
        if remapped in (D.Decision.EDIT_TEXT, D.Decision.EDIT_MEDIA):
            outcome = await self._mediator.apply(
                scope,
                remapped,
                entry,
                base,
                executor=executor,
            )
            if outcome:
                return outcome
        self._telemetry.deny_switch()
        return None


class InlineTextFlow:
    """Handle inline edits when payloads are textual."""

    def __init__(
        self,
        mediator: InlineEditMediator,
        telemetry: InlineTelemetryAdapter,
    ) -> None:
        self._mediator = mediator
        self._telemetry = telemetry

    async def handle(
        self,
        scope: Scope,
        entry: Payload,
        base: Message | None,
        executor: EditExecutor,
    ) -> InlineOutcome | None:
        if base and getattr(base, "media", None):
            adjusted = entry.morph(media=base.media, group=None)
            if self._requires_caption_refresh(adjusted):
                return await self._mediator.apply(
                    scope,
                    D.Decision.EDIT_MEDIA_CAPTION,
                    adjusted,
                    base,
                    executor=executor,
                )
            if not match(getattr(base, "markup", None), getattr(entry, "reply", None)):
                return await self._mediator.apply(
                    scope,
                    D.Decision.EDIT_MARKUP,
                    adjusted,
                    base,
                    executor=executor,
                )
            self._telemetry.deny_switch()
            return None
        return await self._mediator.apply(
            scope,
            D.Decision.EDIT_TEXT,
            entry,
            base,
            executor=executor,
        )

    def _requires_caption_refresh(self, payload: Payload) -> bool:
        extra = payload.extra or {}
        return bool(
            payload.text is not None
            or extra.get("mode") is not None
            or extra.get("entities") is not None
            or extra.get("show_caption_above_media") is not None
        )


@dataclass(slots=True)
class InlineHandler:
    """Mediate inline edits, remapping fallbacks when required."""

    guard: InlineGuard
    remapper: InlineRemapper
    editor: InlineEditor
    telemetry: Telemetry
    _candidate: InlineCandidateBuilder = field(init=False, repr=False)
    _media: InlineMediaFlow = field(init=False, repr=False)
    _text: InlineTextFlow = field(init=False, repr=False)

    def __post_init__(self) -> None:
        adapter = InlineTelemetryAdapter(self.telemetry)
        mediator = InlineEditMediator(self.editor)
        self._candidate = InlineCandidateBuilder()
        self._media = InlineMediaFlow(self.guard, self.remapper, mediator, adapter)
        self._text = InlineTextFlow(mediator, adapter)

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

        entry = self._candidate.create(payload, tail)
        media = getattr(entry, "media", None)

        if media:
            return await self._media.handle(
                scope,
                entry,
                tail,
                executor,
                config,
            )

        return await self._text.handle(scope, entry, tail, executor)


__all__ = [
    "InlineHandler",
    "InlineOutcome",
    "InlineEditor",
    "InlineGuard",
    "InlineRemapper",
]

"""Inline flow coordinators split by media and text handling."""
from __future__ import annotations

from navigator.core.entity.history import Message
from navigator.core.service.rendering import decision as D
from navigator.core.service.rendering.config import RenderingConfig
from navigator.core.service.rendering.helpers import match
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .mediator import InlineEditMediator
from .telemetry import InlineTelemetryAdapter
from .guard import InlineGuard
from .remap import InlineRemapper
from .outcome import InlineOutcome
from ..executor import EditExecutor


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


__all__ = ["InlineMediaFlow", "InlineTextFlow"]

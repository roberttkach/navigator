"""Translate gateway failures into telemetry and fallbacks."""

from __future__ import annotations

from navigator.core.entity.history import Message
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .fallback import FallbackStrategy
from .models import Execution
from .policy import EditErrorPolicy, EditResolutionAction
from .telemetry import EditTelemetry


class EditErrorHandler:
    """Translate gateway failures into telemetry and fallbacks."""

    def __init__(
        self,
        telemetry: EditTelemetry,
        fallback: FallbackStrategy,
        policy: EditErrorPolicy | None = None,
    ) -> None:
        self._telemetry = telemetry
        self._fallback = fallback
        self._policy = policy or EditErrorPolicy()

    async def resolve(
        self,
        error: Exception,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Execution | None:
        resolution = self._policy.resolve(error)
        if resolution is None:
            raise error

        if resolution.skip_reason:
            self._telemetry.skip(resolution.skip_reason)
        if resolution.event:
            self._telemetry.event(resolution.event)
        if resolution.inline_block_reason:
            self._telemetry.inline_blocked(scope, resolution.inline_block_reason)

        if resolution.action is EditResolutionAction.RESEND:
            if scope.inline:
                return None
            return await self._fallback.resend(scope, payload, stem)

        return None


__all__ = ["EditErrorHandler"]


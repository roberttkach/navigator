"""Translate gateway failures into telemetry and fallbacks."""

from __future__ import annotations

from navigator.core.error import (
    CaptionOverflow,
    EditForbidden,
    EmptyPayload,
    ExtraForbidden,
    MessageUnchanged,
    TextOverflow,
)
from navigator.core.entity.history import Message
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .fallback import FallbackStrategy
from .telemetry import EditTelemetry


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
    ) -> "Execution | None":
        from .models import Execution

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


__all__ = ["EditErrorHandler"]


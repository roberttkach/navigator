"""Execute edits while delegating dispatch and error handling."""

from __future__ import annotations

from navigator.core.entity.history import Entry, Message
from navigator.core.error import (
    CaptionOverflow,
    EditForbidden,
    EmptyPayload,
    ExtraForbidden,
    MessageUnchanged,
    TextOverflow,
)
from navigator.core.service.rendering import decision
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .dispatcher import VerdictDispatcher
from .error import EditErrorHandler
from .models import Execution, head

RecoverableEditError = (
    EmptyPayload,
    ExtraForbidden,
    TextOverflow,
    CaptionOverflow,
    EditForbidden,
    MessageUnchanged,
)


class EditOperation:
    """Delegate edit execution to dispatcher and error handling helpers."""

    def __init__(self, dispatcher: VerdictDispatcher, errors: EditErrorHandler) -> None:
        self._dispatcher = dispatcher
        self._errors = errors

    async def apply(
        self,
        scope: Scope,
        verdict: decision.Decision,
        payload: Payload,
        base: Entry | Message | None,
    ) -> Execution | None:
        stem = head(base)

        try:
            if verdict is decision.Decision.NO_CHANGE:
                return None

            return await self._dispatcher.dispatch(verdict, scope, payload, stem)

        except RecoverableEditError as error:
            return await self._errors.resolve(error, scope, payload, stem)


__all__ = ["EditOperation"]


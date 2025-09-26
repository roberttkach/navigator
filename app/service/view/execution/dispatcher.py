"""Dispatch reconciliation decisions to the Telegram gateway."""

from __future__ import annotations

from collections.abc import Awaitable, Callable

from navigator.core.entity.history import Message
from navigator.core.port.message import MessageGateway
from navigator.core.service.rendering import decision
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .fallback import FallbackStrategy
from .models import Execution


class VerdictDispatcher:
    """Dispatch reconciliation decisions to the Telegram gateway."""

    _Handler = Callable[[Scope, Payload, Message | None], Awaitable[Execution | None]]

    def __init__(
        self,
        gateway: MessageGateway,
        *,
        fallback: FallbackStrategy | None = None,
    ) -> None:
        self._gateway = gateway
        self._fallback = fallback or FallbackStrategy(gateway)
        self._handlers: dict[decision.Decision, VerdictDispatcher._Handler] = {
            decision.Decision.RESEND: self._send,
            decision.Decision.EDIT_TEXT: self._rewrite,
            decision.Decision.EDIT_MEDIA: self._recast,
            decision.Decision.EDIT_MEDIA_CAPTION: self._retitle,
            decision.Decision.EDIT_MARKUP: self._remap,
            decision.Decision.DELETE_SEND: self._delete_and_send,
        }

    async def dispatch(
        self,
        verdict: decision.Decision,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Execution | None:
        handler = self._handlers.get(verdict)
        if handler is None:
            return None
        return await handler(scope, payload, stem)

    async def _send(self, scope: Scope, payload: Payload, stem: Message | None) -> Execution:
        result = await self._gateway.send(scope, payload)
        return Execution(result=result, stem=stem)

    async def _rewrite(
        self,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Execution | None:
        if not stem:
            return None
        result = await self._gateway.rewrite(scope, stem.id, payload)
        return Execution(result=result, stem=stem)

    async def _recast(
        self,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Execution | None:
        if not stem:
            return None
        result = await self._gateway.recast(scope, stem.id, payload)
        return Execution(result=result, stem=stem)

    async def _retitle(
        self,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Execution | None:
        if not stem:
            return None
        result = await self._gateway.retitle(scope, stem.id, payload)
        return Execution(result=result, stem=stem)

    async def _remap(
        self,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Execution | None:
        if not stem:
            return None
        result = await self._gateway.remap(scope, stem.id, payload)
        return Execution(result=result, stem=stem)

    async def _delete_and_send(
        self,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> Execution:
        return await self._fallback.resend(scope, payload, stem)


__all__ = ["VerdictDispatcher"]


"""Fallback helpers used when Telegram rejects edit operations."""

from __future__ import annotations

from dataclasses import dataclass

from navigator.core.entity.history import Message
from navigator.core.port.message import MessageGateway
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope


def _targets(message: Message | None) -> list[int]:
    """Collect identifiers that need deletion after resend fallbacks."""

    if not message:
        return []
    bundle = [int(message.id)]
    bundle.extend(int(x) for x in (message.extras or []))
    return bundle


@dataclass(slots=True)
class FallbackStrategy:
    """Coordinate fallback resend operations when edits are forbidden."""

    gateway: MessageGateway

    async def resend(
        self,
        scope: Scope,
        payload: Payload,
        stem: Message | None,
    ) -> "Execution":
        from .models import Execution

        result = await self.gateway.send(scope, payload)
        if stem:
            await self.gateway.delete(scope, _targets(stem))
        return Execution(result=result, stem=stem)


__all__ = ["FallbackStrategy"]


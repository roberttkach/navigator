"""Tail-related helpers used by the navigator runtime."""
from __future__ import annotations

from navigator.app.dto.content import Content

from .tail_components import TailGateway, TailLocker, TailTelemetry


class NavigatorTail:
    """Expose tail operations guarded by telemetry and locking."""

    def __init__(
        self,
        *,
        gateway: TailGateway,
        locker: TailLocker,
        telemetry: TailTelemetry,
    ) -> None:
        self._gateway = gateway
        self._locker = locker
        self._telemetry = telemetry

    async def get(self) -> dict[str, object] | None:
        self._telemetry.emit("last.get")
        async with self._locker.acquire():
            identifier = await self._gateway.peek()
        if identifier is None:
            return None
        return {
            "id": identifier,
            "inline": bool(self._locker.scope.inline),
            "chat": self._locker.scope.chat,
        }

    async def delete(self) -> None:
        self._telemetry.emit("last.delete")
        async with self._locker.acquire() as scope:
            await self._gateway.delete(scope)

    async def edit(self, content: Content) -> int | None:
        self._telemetry.emit(
            "last.edit",
            payload={
                "text": bool(content.text),
                "media": bool(content.media),
                "group": bool(content.group),
            },
        )
        async with self._locker.acquire() as scope:
            result = await self._gateway.edit(scope, content)
        return result


__all__ = ["NavigatorTail"]

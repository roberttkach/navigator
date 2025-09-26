"""Tail-related helpers used by the navigator runtime."""
from __future__ import annotations

from .tail_components import (
    TailEditRequest,
    TailGateway,
    TailLocker,
    TailTelemetry,
)
from .tail_view import TailView


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

    async def get(self) -> TailView | None:
        self._telemetry.emit("last.get")
        async with self._locker.acquire():
            identifier = await self._gateway.peek()
        if identifier is None:
            return None
        return TailView(
            identifier=identifier,
            inline=bool(self._locker.scope.inline),
            chat=self._locker.scope.chat,
        )

    async def delete(self) -> None:
        self._telemetry.emit("last.delete")
        async with self._locker.acquire() as scope:
            await self._gateway.delete(scope)

    async def edit(self, request: TailEditRequest) -> int | None:
        description = request.describe()
        self._telemetry.emit(
            "last.edit",
            payload={
                "text": description.text,
                "media": description.media,
                "group": description.group,
            },
        )
        async with self._locker.acquire() as scope:
            result = await self._gateway.edit(scope, request)
        return result


__all__ = ["NavigatorTail"]

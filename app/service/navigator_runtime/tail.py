"""Tail-related helpers used by the navigator runtime."""
from __future__ import annotations

from .tail_components import (
    TailEditRequest,
    TailGateway,
    TailLocker,
    TailTelemetry,
    TailViewFactory,
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
        view_factory: TailViewFactory,
    ) -> None:
        self._gateway = gateway
        self._locker = locker
        self._telemetry = telemetry
        self._view_factory = view_factory

    async def get(self) -> TailView | None:
        self._telemetry.record_get()
        async with self._locker.acquire() as scope:
            identifier = await self._gateway.peek()
        if identifier is None:
            return None
        return self._view_factory.create(scope=scope, identifier=identifier)

    async def delete(self) -> None:
        self._telemetry.record_delete()
        async with self._locker.acquire() as scope:
            await self._gateway.delete(scope)

    async def edit(self, request: TailEditRequest) -> int | None:
        description = request.describe()
        self._telemetry.record_edit(description)
        async with self._locker.acquire() as scope:
            return await self._gateway.edit(scope, request)


__all__ = ["NavigatorTail"]

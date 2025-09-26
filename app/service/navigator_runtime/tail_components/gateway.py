"""Adapter bridging navigator tail use cases with runtime services."""
from __future__ import annotations

from navigator.core.value.message import Scope

from navigator.app.service.navigator_runtime.tail_components.edit_request import (
    TailEditRequest,
)
from navigator.app.service.navigator_runtime.tail_components.converter import (
    TailPayloadConverter,
)
from navigator.app.usecase.last import Tailer


class TailGateway:
    """Adapt navigator tail use cases for runtime consumption."""

    def __init__(self, flow: Tailer, *, converter: TailPayloadConverter | None = None) -> None:
        self._flow = flow
        self._converter = converter or TailPayloadConverter()

    async def peek(self) -> int | None:
        return await self._flow.peek()

    async def delete(self, scope: Scope) -> None:
        await self._flow.delete(scope)

    async def edit(self, scope: Scope, request: TailEditRequest) -> int | None:
        payload = request.payload(self._converter)
        return await self._flow.edit(scope, payload)


__all__ = ["TailGateway"]

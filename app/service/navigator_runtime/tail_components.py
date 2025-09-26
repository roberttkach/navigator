"""Supporting collaborators for navigator tail operations."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import AsyncIterator

from navigator.app.dto.content import Content
from navigator.app.locks.guard import Guardian
from navigator.app.map.payload import convert
from navigator.app.usecase.last import Tailer
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.service.scope import profile
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope


class TailPayloadConverter:
    """Translate tail DTOs into payloads accepted by the use case flow."""

    def convert(self, content: Content) -> Payload:
        return convert(content)


class TailGateway:
    """Adapt navigator tail use cases for runtime consumption."""

    def __init__(self, flow: Tailer, *, converter: TailPayloadConverter | None = None) -> None:
        self._flow = flow
        self._converter = converter or TailPayloadConverter()

    async def peek(self) -> int | None:
        return await self._flow.peek()

    async def delete(self, scope: Scope) -> None:
        await self._flow.delete(scope)

    async def edit(self, scope: Scope, content: Content) -> int | None:
        payload = self._converter.convert(content)
        return await self._flow.edit(scope, payload)


class TailTelemetry:
    """Emit structured telemetry for navigator tail operations."""

    def __init__(self, channel: TelemetryChannel, *, scope: Scope) -> None:
        self._channel = channel
        self._profile = profile(scope)

    @classmethod
    def from_telemetry(cls, telemetry: Telemetry, scope: Scope) -> "TailTelemetry":
        channel = telemetry.channel(__name__)
        return cls(channel, scope=scope)

    def emit(self, method: str, **fields: object) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method=method,
            scope=self._profile,
            **fields,
        )


class TailLocker:
    """Provide a scoped guard context for navigator tail operations."""

    def __init__(self, guard: Guardian, scope: Scope) -> None:
        self._guard = guard
        self._scope = scope

    @property
    def scope(self) -> Scope:
        return self._scope

    @asynccontextmanager
    async def acquire(self) -> AsyncIterator[Scope]:
        async with self._guard(self._scope):
            yield self._scope


__all__ = [
    "TailGateway",
    "TailLocker",
    "TailPayloadConverter",
    "TailTelemetry",
]


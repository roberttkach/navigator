"""Tail-related helpers used by the navigator runtime."""
from __future__ import annotations

import logging

from navigator.app.dto.content import Content
from navigator.app.locks.guard import Guardian
from navigator.app.usecase.last import Tailer
from navigator.app.map.payload import convert
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.service.scope import profile
from navigator.core.value.message import Scope


class NavigatorTail:
    """Expose tail operations guarded by telemetry and locking."""

    def __init__(
        self,
        *,
        flow: Tailer,
        scope: Scope,
        guard: Guardian,
        telemetry: Telemetry,
    ) -> None:
        self._tailer = flow
        self._scope = scope
        self._guard = guard
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._profile = profile(scope)

    async def get(self) -> dict[str, object] | None:
        self._emit("last.get")
        async with self._guard(self._scope):
            identifier = await self._tailer.peek()
        if identifier is None:
            return None
        return {
            "id": identifier,
            "inline": bool(self._scope.inline),
            "chat": self._scope.chat,
        }

    async def delete(self) -> None:
        self._emit("last.delete")
        async with self._guard(self._scope):
            await self._tailer.delete(self._scope)

    async def edit(self, content: Content) -> int | None:
        self._emit(
            "last.edit",
            payload={
                "text": bool(content.text),
                "media": bool(content.media),
                "group": bool(content.group),
            },
        )
        async with self._guard(self._scope):
            result = await self._tailer.edit(self._scope, convert(content))
        return result

    def _emit(self, method: str, **fields: object) -> None:
        self._channel.emit(
            logging.INFO,
            LogCode.NAVIGATOR_API,
            method=method,
            scope=self._profile,
            **fields,
        )


__all__ = ["NavigatorTail"]

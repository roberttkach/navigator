"""State management helpers for the restoration workflow."""
from __future__ import annotations

import logging
from typing import Any

from navigator.app.service.view.restorer import ViewRestorer
from navigator.core.entity.history import Entry
from navigator.core.port.state import StateRepository
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.content import Payload, normalize


class StateSynchronizer:
    """Synchronise persistent state assignments with telemetry."""

    def __init__(self, state: StateRepository, telemetry: Telemetry) -> None:
        self._state = state
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.state")

    async def assign(self, entry: Entry) -> None:
        await self._state.assign(entry.state)
        self._channel.emit(
            logging.INFO,
            LogCode.STATE_SET,
            op="set",
            state={"target": entry.state},
        )

    async def snapshot(self) -> dict[str, Any]:
        memory = await self._state.payload()
        return memory or {}


class PayloadReviver:
    """Merge stored context with fresh data and revive payloads."""

    def __init__(self, synchronizer: StateSynchronizer, restorer: ViewRestorer) -> None:
        self._synchronizer = synchronizer
        self._restorer = restorer

    async def revive(
        self,
        entry: Entry,
        context: dict[str, Any],
        *,
        inline: bool,
    ) -> list[Payload]:
        memory = await self._synchronizer.snapshot()
        merged = {**memory, **context}
        restored = await self._restorer.revive(entry, merged, inline=inline)
        return [normalize(payload) for payload in restored]


__all__ = ["PayloadReviver", "StateSynchronizer"]

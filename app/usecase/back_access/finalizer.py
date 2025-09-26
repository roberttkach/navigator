"""Finalization helpers orchestrating rewind write operations."""
from __future__ import annotations

import logging
from collections.abc import Sequence

from navigator.core.entity.history import Entry
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel

from .mutator import RewindMutator
from .writer import RewindHistoryWriter
from .utils import trim


class RewindFinalizer:
    """Persist rewind outcomes while emitting telemetry."""

    def __init__(
        self,
        writer: RewindHistoryWriter,
        mutator: RewindMutator,
        telemetry: Telemetry,
    ) -> None:
        self._writer = writer
        self._mutator = mutator
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.finalizer")

    async def skip(self, history: Sequence[Entry], target: Entry) -> None:
        """Handle rewind sequences that do not trigger mutations."""

        self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="back")
        await self._writer.assign_state(target.state)
        marker = target.messages[0].id if target.messages else None
        await self._writer.mark_latest(int(marker) if marker is not None else None)
        await self._writer.archive(trim(history))

    async def apply(self, history: Sequence[Entry], target: Entry, render: object) -> None:
        """Persist rebuilt entries and update state markers."""

        snapshot = list(trim(history))
        rebuilt = self._mutator.rebuild(target, render)
        if snapshot:
            snapshot[-1] = rebuilt
        else:  # pragma: no cover - defensive guard
            snapshot.append(rebuilt)
        await self._writer.archive(snapshot)
        await self._writer.assign_state(target.state)
        identifier = self._mutator.primary_identifier(render)
        await self._writer.mark_latest(identifier)

"""Support objects used by the ``back`` use case.

These helpers encapsulate data access and transformation logic that was
previously concentrated inside :class:`navigator.app.usecase.back.Rewinder`.
Splitting responsibilities keeps the coordinator lean and makes the
individual steps easier to test in isolation.
"""

from __future__ import annotations

import logging
from collections.abc import Iterable, Sequence
from dataclasses import replace
from typing import Any

from navigator.app.service.view.planner import ViewPlanner
from navigator.app.service.view.restorer import ViewRestorer
from navigator.core.entity.history import Entry
from navigator.core.error import HistoryEmpty
from navigator.core.port.history import HistoryRepository
from navigator.core.port.last import LatestRepository
from navigator.core.port.state import StateRepository
from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope

_MIN_HISTORY_LENGTH = 2


class RewindHistoryReader:
    """Expose read-only history operations required during rewind."""

    def __init__(
        self,
        ledger: HistoryRepository,
        status: StateRepository,
        telemetry: Telemetry,
    ) -> None:
        self._ledger = ledger
        self._status = status
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.history.read")

    async def snapshot(self, scope: Scope) -> list[Entry]:
        """Return the current history snapshot while logging telemetry."""

        history = await self._ledger.recall()
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="back",
            history={"len": len(history)},
            scope=profile(scope),
        )
        return history

    def select(self, history: Sequence[Entry]) -> tuple[Entry, Entry]:
        """Return the current and previous entries in ``history``."""

        if len(history) < _MIN_HISTORY_LENGTH:
            raise HistoryEmpty("Cannot go back, history is too short.")
        return history[-1], history[-2]

    async def payload(self) -> dict[str, Any]:
        """Return persisted state payload used for restore operations."""

        return await self._status.payload()


class RewindHistoryWriter:
    """Persist rewind side-effects while emitting telemetry."""

    def __init__(
        self,
        ledger: HistoryRepository,
        status: StateRepository,
        latest: LatestRepository,
        telemetry: Telemetry,
    ) -> None:
        self._ledger = ledger
        self._status = status
        self._latest = latest
        self._channel: TelemetryChannel = telemetry.channel(f"{__name__}.history.write")

    async def assign_state(self, state: str | None) -> None:
        """Persist ``state`` and report bookkeeping telemetry."""

        if state is None:
            return
        await self._status.assign(state)
        self._channel.emit(
            logging.INFO,
            LogCode.STATE_SET,
            op="back",
            state={"target": state},
        )

    async def mark_latest(self, identifier: int | None) -> None:
        """Mark ``identifier`` as the latest message when provided."""

        if identifier is None:
            return
        await self._latest.mark(identifier)
        self._channel.emit(
            logging.INFO,
            LogCode.LAST_SET,
            op="back",
            message={"id": identifier},
        )

    async def archive(self, history: Sequence[Entry]) -> None:
        """Persist ``history`` snapshot with telemetry."""

        snapshot = list(history)
        await self._ledger.archive(snapshot)
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op="back",
            history={"len": len(snapshot)},
        )


class RewindRenderer:
    """Handle payload revive and render planning for rewind."""

    def __init__(
            self,
            restorer: ViewRestorer,
            planner: ViewPlanner,
    ) -> None:
        self._restorer = restorer
        self._planner = planner

    async def revive(
        self,
        target: Entry,
        context: dict[str, Any],
        memory: dict[str, Any],
        *,
        inline: bool,
    ) -> list[Any]:
        merged = {**memory, **context}
        revived = await self._restorer.revive(target, merged, inline=inline)
        return [*revived]

    async def render(
        self,
        scope: Scope,
        payloads: list[Any],
        origin: Entry,
        *,
        inline: bool,
    ) -> object:
        return await self._planner.render(
            scope,
            payloads,
            origin,
            inline=inline,
        )


class RewindMutator:
    """Mutate entries using render metadata."""

    def rebuild(self, target: Entry, render: object) -> Entry:
        identifiers = self.identifiers(render)
        extras = self.extras(render)
        limit = min(len(target.messages), len(identifiers))
        messages = list(target.messages)

        for index in range(limit):
            message = target.messages[index]
            provided = (
                extras[index]
                if index < len(extras)
                else list(message.extras or [])
            )
            messages[index] = replace(
                message,
                id=int(identifiers[index]),
                extras=list(provided),
            )

        return replace(target, messages=messages)

    def identifiers(self, render: object) -> list[int]:
        raw = getattr(render, "ids", None) or []
        return [int(identifier) for identifier in raw]

    def extras(self, render: object) -> list[list[int]]:
        raw = getattr(render, "extras", None) or []
        return [list(extra) for extra in raw]

    def primary_identifier(self, render: object) -> int | None:
        identifiers = self.identifiers(render)
        return identifiers[0] if identifiers else None


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


def trim(history: Sequence[Entry]) -> Iterable[Entry]:
    """Yield history entries without the latest snapshot."""

    yield from history[:-1]


__all__ = [
    "RewindHistoryReader",
    "RewindHistoryWriter",
    "RewindMutator",
    "RewindRenderer",
    "RewindFinalizer",
    "trim",
]

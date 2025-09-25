"""Support objects used by the ``back`` use case.

These helpers encapsulate data access and transformation logic that was
previously concentrated inside :class:`navigator.app.usecase.back.Rewinder`.
Splitting responsibilities keeps the coordinator lean and makes the
individual steps easier to test in isolation.
"""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any, Dict, Iterable, List, Sequence, Tuple

from navigator.app.service.view.restorer import ViewRestorer
from navigator.app.service.view.planner import ViewPlanner
from navigator.core.entity.history import Entry
from navigator.core.error import HistoryEmpty
from navigator.core.port.history import HistoryRepository
from navigator.core.port.last import LatestRepository
from navigator.core.port.state import StateRepository
from navigator.core.service.scope import profile
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.value.message import Scope


class RewindHistoryAccess:
    """Expose history/state operations required during rewind."""

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
        self._channel: TelemetryChannel = telemetry.channel(
            f"{__name__}.history"
        )

    async def snapshot(self, scope: Scope) -> List[Entry]:
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

    def select(self, history: Sequence[Entry]) -> Tuple[Entry, Entry]:
        """Return the current and previous entries in ``history``."""

        if len(history) < 2:
            raise HistoryEmpty("Cannot go back, history is too short.")
        return history[-1], history[-2]

    async def payload(self) -> Dict[str, Any]:
        """Return persisted state payload used for restore operations."""

        return await self._status.payload()

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
            context: Dict[str, Any],
            memory: Dict[str, Any],
            *,
            inline: bool,
    ) -> List[Any]:
        merged = {**memory, **context}
        revived = await self._restorer.revive(target, merged, inline=inline)
        return [*revived]

    async def render(
            self,
            scope: Scope,
            payloads: List[Any],
            origin: Entry,
            *,
            inline: bool,
    ) -> Any:
        return await self._planner.render(
            scope,
            payloads,
            origin,
            inline=inline,
        )


class RewindMutator:
    """Mutate entries using render metadata."""

    def rebuild(self, target: Entry, render: Any) -> Entry:
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

    def identifiers(self, render: Any) -> List[int]:
        raw = getattr(render, "ids", None) or []
        return [int(identifier) for identifier in raw]

    def extras(self, render: Any) -> List[List[int]]:
        raw = getattr(render, "extras", None) or []
        return [list(extra) for extra in raw]

    def primary_identifier(self, render: Any) -> int | None:
        identifiers = self.identifiers(render)
        return identifiers[0] if identifiers else None


def trim(history: Sequence[Entry]) -> Iterable[Entry]:
    """Yield history entries without the latest snapshot."""

    yield from history[:-1]


__all__ = [
    "RewindHistoryAccess",
    "RewindMutator",
    "RewindRenderer",
    "trim",
]

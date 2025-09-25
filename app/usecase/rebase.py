"""Rebase the latest entry marker onto a supplied message identifier."""

from __future__ import annotations

import logging
from typing import List

from ..log import events
from ..log.aspect import TraceAspect
from ...core.entity.history import Entry, Message
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel


class Shifter:
    """Shift the latest message marker to a newly provided ``marker``."""

    def __init__(self, ledger: HistoryRepository, latest: LatestRepository, telemetry: Telemetry):
        self._ledger = ledger
        self._latest = latest
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._trace = TraceAspect(telemetry)

    async def execute(self, marker: int) -> None:
        """Rebase history marker onto ``marker`` value."""

        await self._trace.run(events.REBASE, self._perform, marker)

    async def _perform(self, marker: int) -> None:
        history = await self._load_history()
        if not history:
            return

        last = history[-1]
        if not last.messages:
            await self._update_marker_only(marker, len(history))
            return

        rebuilt = self._patch_entry(history, last, marker)
        await self._persist(rebuilt, marker)

    async def _load_history(self) -> List[Entry]:
        """Return history snapshots while emitting telemetry."""

        history = await self._ledger.recall()
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="rebase",
            history={"len": len(history)},
        )
        return history

    async def _update_marker_only(self, marker: int, history_len: int) -> None:
        """Update latest marker when history has no persisted messages."""

        await self._latest.mark(int(marker))
        self._channel.emit(
            logging.INFO,
            LogCode.LAST_SET,
            op="rebase",
            message={"id": int(marker)},
        )
        self._channel.emit(
            logging.INFO,
            LogCode.REBASE_SUCCESS,
            op="rebase",
            message={"id": int(marker)},
            history={"len": history_len},
        )

    def _patch_entry(self, history: List[Entry], last: Entry, marker: int) -> List[Entry]:
        """Return rebuilt history with ``last`` message id replaced."""

        first = last.messages[0]
        patched = Message(
            id=int(marker),
            text=first.text,
            media=first.media,
            group=first.group,
            markup=first.markup,
            preview=first.preview,
            extra=first.extra,
            extras=first.extras,
            inline=first.inline,
            automated=first.automated,
            ts=first.ts,
        )
        trailer = Entry(
            state=last.state,
            view=last.view,
            messages=[patched, *last.messages[1:]],
            root=last.root,
        )
        rebuilt: List[Entry] = [*history[:-1], trailer]
        return rebuilt

    async def _persist(self, rebuilt: List[Entry], marker: int) -> None:
        """Persist rebuilt history snapshot and update marker telemetry."""

        await self._ledger.archive(rebuilt)
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op="rebase",
            history={"len": len(rebuilt)},
        )
        await self._latest.mark(int(marker))
        self._channel.emit(
            logging.INFO,
            LogCode.LAST_SET,
            op="rebase",
            message={"id": int(marker)},
        )
        self._channel.emit(
            logging.INFO,
            LogCode.REBASE_SUCCESS,
            op="rebase",
            message={"id": int(marker)},
            history={"len": len(rebuilt)},
        )

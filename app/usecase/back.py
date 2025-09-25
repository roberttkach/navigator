"""Restore the previous history entry and re-render when needed."""

from __future__ import annotations

import logging
from dataclasses import replace
from typing import Any, Dict, List, Sequence, Tuple

from ..log import events
from ..log.aspect import TraceAspect
from ..service.view.planner import ViewPlanner
from ..service.view.restorer import ViewRestorer
from ...core.entity.history import Entry
from ...core.error import HistoryEmpty
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from ...core.port.message import MessageGateway
from ...core.port.state import StateRepository
from ...core.service.scope import profile
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import normalize
from ...core.value.message import Scope


class Rewinder:
    """Coordinate rewind operations for conversation history."""

    def __init__(
            self,
            ledger: HistoryRepository,
            status: StateRepository,
            gateway: MessageGateway,
            restorer: ViewRestorer,
            planner: ViewPlanner,
            latest: LatestRepository,
            telemetry: Telemetry,
    ) -> None:
        self._ledger = ledger
        self._status = status
        self._gateway = gateway
        self._restorer = restorer
        self._planner = planner
        self._latest = latest
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._trace = TraceAspect(telemetry)

    async def execute(self, scope: Scope, context: Dict[str, Any]) -> None:
        """Rewind the history for ``scope`` using extra ``context`` hints."""

        await self._trace.run(events.BACK, self._perform, scope, context)

    async def _perform(self, scope: Scope, context: Dict[str, Any]) -> None:
        history = await self._load_history(scope)
        origin, target = self._select_targets(history)
        inline = bool(scope.inline)
        restored = await self._restore_payloads(target, context, inline)
        resolved = [normalize(payload) for payload in restored]
        render = await self._render(scope, resolved, origin, inline)

        if not render or not getattr(render, "changed", False):
            await self._handle_skip(history, target)
            return

        rebuilt = self._patch_entry(target, render)
        await self._finalize(history, rebuilt, target, render)

    async def _load_history(self, scope: Scope) -> List[Entry]:
        """Return history snapshot while emitting telemetry."""

        history = await self._ledger.recall()
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="back",
            history={"len": len(history)},
            scope=profile(scope),
        )
        return history

    def _select_targets(self, history: Sequence[Entry]) -> Tuple[Entry, Entry]:
        """Return current and previous entries ensuring rewind is valid."""

        if len(history) < 2:
            raise HistoryEmpty("Cannot go back, history is too short.")
        return history[-1], history[-2]

    async def _restore_payloads(
            self,
            target: Entry,
            context: Dict[str, Any],
            inline: bool,
    ) -> List[Any]:
        """Revive payloads using stored state merged with ``context``."""

        memory: Dict[str, Any] = await self._status.payload()
        merged = {**memory, **context}
        revived = await self._restorer.revive(target, merged, inline=inline)
        return [*revived]

    async def _render(
            self,
            scope: Scope,
            payloads: List[Any],
            origin: Entry,
            inline: bool,
    ) -> Any:
        """Render ``payloads`` against ``origin`` entry respecting inline mode."""

        return await self._planner.render(
            scope,
            payloads,
            origin,
            inline=inline,
        )

    async def _handle_skip(self, history: Sequence[Entry], target: Entry) -> None:
        """Handle rewind when no rendering changes are required."""

        self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="back")
        await self._status.assign(target.state)
        if not target.messages:
            return

        marker = int(target.messages[0].id)
        await self._latest.mark(marker)
        trimmed = list(history[:-1])
        await self._archive(trimmed)

    def _patch_entry(self, target: Entry, render: Any) -> Entry:
        """Return ``target`` with messages patched using ``render`` metadata."""

        identifiers = self._identifiers(render)
        extras = self._extras(render)
        limit = min(len(target.messages), len(identifiers))
        messages = list(target.messages)

        for index in range(limit):
            message = target.messages[index]
            provided = extras[index] if index < len(extras) else list(message.extras or [])
            messages[index] = replace(
                message,
                id=int(identifiers[index]),
                extras=list(provided),
            )

        return replace(target, messages=messages)

    async def _finalize(
            self,
            history: Sequence[Entry],
            rebuilt: Entry,
            target: Entry,
            render: Any,
    ) -> None:
        """Persist rebuilt entry and update state/marker telemetry."""

        trimmed = list(history[:-1])
        trimmed[-1] = rebuilt
        await self._archive(trimmed)
        await self._status.assign(target.state)
        self._channel.emit(
            logging.INFO,
            LogCode.STATE_SET,
            op="back",
            state={"target": target.state},
        )
        identifiers = self._identifiers(render)
        if not identifiers:
            return
        await self._latest.mark(identifiers[0])
        self._channel.emit(
            logging.INFO,
            LogCode.LAST_SET,
            op="back",
            message={"id": identifiers[0]},
        )

    def _identifiers(self, render: Any) -> List[int]:
        """Return integer identifiers extracted from ``render`` metadata."""

        raw = getattr(render, "ids", None) or []
        return [int(identifier) for identifier in raw]

    def _extras(self, render: Any) -> List[List[int]]:
        """Return extras extracted from ``render`` metadata."""

        raw = getattr(render, "extras", None) or []
        return [list(extra) for extra in raw]

    async def _archive(self, history: Sequence[Entry]) -> None:
        """Persist ``history`` snapshot with telemetry bookkeeping."""

        snapshot = list(history)
        await self._ledger.archive(snapshot)
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op="back",
            history={"len": len(snapshot)},
        )

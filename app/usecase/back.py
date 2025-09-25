from __future__ import annotations

import logging
from typing import Any, Dict

from ..log import events
from ..log.aspect import TraceAspect
from ..service.view.planner import ViewPlanner
from ..service.view.restorer import ViewRestorer
from ...core.error import HistoryEmpty
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from ...core.port.message import MessageGateway
from ...core.port.state import StateRepository
from ...core.telemetry import LogCode, Telemetry, TelemetryChannel
from ...core.value.content import normalize
from ...core.value.message import Scope


class Rewinder:
    def __init__(
            self,
            ledger: HistoryRepository,
            status: StateRepository,
            gateway: MessageGateway,
            restorer: ViewRestorer,
            planner: ViewPlanner,
            latest: LatestRepository,
            telemetry: Telemetry,
    ):
        self._ledger = ledger
        self._status = status
        self._gateway = gateway
        self._restorer = restorer
        self._planner = planner
        self._latest = latest
        self._channel: TelemetryChannel = telemetry.channel(__name__)
        self._trace = TraceAspect(telemetry)

    async def execute(self, scope: Scope, context: Dict[str, Any]) -> None:
        await self._trace.run(events.BACK, self._perform, scope, context)

    async def _perform(self, scope: Scope, context: Dict[str, Any]) -> None:
        history = await self._ledger.recall()
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="back",
            history={"len": len(history)},
            scope={"chat": scope.chat, "inline": bool(scope.inline)},
        )
        if len(history) < 2:
            raise HistoryEmpty("Cannot go back, history is too short.")
        origin = history[-1]
        target = history[-2]
        inline = bool(scope.inline)
        memory: Dict[str, Any] = await self._status.payload()
        merged = {**memory, **context}
        restored = await self._restorer.revive(target, merged, inline=inline)
        resolved = [normalize(p) for p in restored]
        if not inline:
            render = await self._planner.render(
                scope,
                resolved,
                origin,
                inline=False,
            )
        else:
            render = await self._planner.render(
                scope,
                resolved,
                origin,
                inline=True,
            )

        if not render or not render.changed:
            self._channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="back")
            await self._status.assign(target.state)
            if target.messages:
                marker = target.messages[0].id
                await self._latest.mark(marker)
                trimmed = history[:-1]
                await self._ledger.archive(trimmed)
                self._channel.emit(
                    logging.DEBUG,
                    LogCode.HISTORY_SAVE,
                    op="back",
                    history={"len": len(trimmed)},
                )
            return
        limit = min(len(target.messages), len(render.ids))
        patched = [
            type(target.messages[i])(
                id=render.ids[i],
                text=target.messages[i].text,
                media=target.messages[i].media,
                group=target.messages[i].group,
                markup=target.messages[i].markup,
                preview=target.messages[i].preview,
                extra=target.messages[i].extra,
                extras=render.extras[i],
                inline=target.messages[i].inline,
                automated=target.messages[i].automated,
                ts=target.messages[i].ts,
            )
            for i in range(limit)
        ]
        merged = patched + target.messages[limit:]
        rebuilt = type(target)(
            state=target.state,
            view=target.view,
            messages=merged,
            root=target.root,
        )
        trimmed = history[:-1]
        trimmed[-1] = rebuilt
        await self._ledger.archive(trimmed)
        self._channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op="back",
            history={"len": len(trimmed)},
        )
        await self._status.assign(target.state)
        self._channel.emit(
            logging.INFO,
            LogCode.STATE_SET,
            op="back",
            state={"target": target.state},
        )
        await self._latest.mark(render.ids[0])
        self._channel.emit(
            logging.INFO,
            LogCode.LAST_SET,
            op="back",
            message={"id": render.ids[0]},
        )

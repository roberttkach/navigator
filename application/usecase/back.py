from __future__ import annotations

import logging
from typing import Any, Dict

from ..log.decorators import trace
from navigator.logging import LogCode, jlog
from ..service.view.planner import ViewPlanner
from ..service.view.restorer import ViewRestorer
from ...domain.error import HistoryEmpty
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LatestRepository
from ...domain.port.message import MessageGateway
from ...domain.port.state import StateRepository
from ...domain.value.content import normalize
from ...domain.value.message import Scope

logger = logging.getLogger(__name__)


class Rewinder:
    def __init__(
            self,
            ledger: HistoryRepository,
            status: StateRepository,
            gateway: MessageGateway,
            restorer: ViewRestorer,
            planner: ViewPlanner,
            latest: LatestRepository,
    ):
        self._ledger = ledger
        self._status = status
        self._gateway = gateway
        self._restorer = restorer
        self._planner = planner
        self._latest = latest

    @trace(None, None, None)
    async def execute(self, scope: Scope, context: Dict[str, Any]) -> None:
        history = await self._ledger.recall()
        jlog(
            logger,
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
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="back")
            await self._status.assign(target.state)
            if target.messages:
                marker = target.messages[0].id
                await self._latest.mark(marker)
            trimmed = history[:-1]
            await self._ledger.archive(trimmed)
            jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="back", history={"len": len(trimmed)})
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
        jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="back", history={"len": len(trimmed)})
        await self._status.assign(target.state)
        jlog(logger, logging.INFO, LogCode.STATE_SET, op="back", state={"target": target.state})
        await self._latest.mark(render.ids[0])
        jlog(logger, logging.INFO, LogCode.LAST_SET, op="back", message={"id": render.ids[0]})

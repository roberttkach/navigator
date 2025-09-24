from __future__ import annotations

import logging
from typing import Any, Dict, Optional

from ..log.decorators import trace
from ...core.telemetry import LogCode, telemetry
from ..service.view.planner import ViewPlanner
from ..service.view.restorer import ViewRestorer
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from ...core.port.message import MessageGateway
from ...core.port.state import StateRepository
from ...core.value.content import normalize
from ...core.value.message import Scope
from ...core.error import StateNotFound

channel = telemetry.channel(__name__)


class Setter:
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
    async def execute(
            self,
            scope: Scope,
            goal: str,
            context: Dict[str, Any],
    ) -> None:
        history = await self._ledger.recall()
        channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="set",
            history={"len": len(history)},
            scope={"chat": scope.chat, "inline": bool(scope.inline)},
        )
        cursor: Optional[int] = None
        for i in range(len(history) - 1, -1, -1):
            if history[i].state == goal:
                cursor = i
                break
        if cursor is None:
            raise StateNotFound(goal)
        target = history[cursor]
        inline = bool(scope.inline)
        tail = history[-1]
        trimmed = history[: cursor + 1]
        await self._ledger.archive(trimmed)
        channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op="set",
            history={"len": len(trimmed)},
        )
        await self._status.assign(target.state)
        channel.emit(
            logging.INFO,
            LogCode.STATE_SET,
            op="set",
            state={"target": target.state},
        )
        memory = await self._status.payload()
        merged = {**memory, **context}
        restored = await self._restorer.revive(target, merged, inline=inline)
        resolved = [normalize(p) for p in restored]
        if not inline:
            render = await self._planner.render(
                scope,
                resolved,
                tail,
                inline=False,
            )
        else:
            render = await self._planner.render(
                scope,
                resolved,
                tail,
                inline=True,
            )
        if render and render.changed:
            current = await self._ledger.recall()
            if current:
                tail = current[-1]
                patched = type(tail)(
                    state=tail.state,
                    view=tail.view,
                    messages=[
                        type(tail.messages[i])(
                            id=render.ids[i],
                            text=tail.messages[i].text,
                            media=tail.messages[i].media,
                            group=tail.messages[i].group,
                            markup=tail.messages[i].markup,
                            preview=tail.messages[i].preview,
                            extra=tail.messages[i].extra,
                            extras=render.extras[i],
                            inline=tail.messages[i].inline,
                            automated=tail.messages[i].automated,
                            ts=tail.messages[i].ts,
                        )
                        for i in range(min(len(tail.messages), len(render.ids)))
                    ]
                    + tail.messages[min(len(tail.messages), len(render.ids)):],
                    root=tail.root,
                )
                await self._ledger.archive(current[:-1] + [patched])
                channel.emit(
                    logging.DEBUG,
                    LogCode.HISTORY_SAVE,
                    op="set",
                    history={"len": len(current)},
                )
            await self._latest.mark(render.ids[0])
            channel.emit(
                logging.INFO,
                LogCode.LAST_SET,
                op="set",
                message={"id": render.ids[0]},
            )
        else:
            channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="set")
            current = await self._ledger.recall()
            tail = current[-1] if current else target
            if tail.messages:
                await self._latest.mark(tail.messages[0].id)
            return

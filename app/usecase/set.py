from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from ..log.decorators import trace
from ...core.error import StateNotFound
from ...core.port.history import HistoryRepository
from ...core.port.last import LatestRepository
from ...core.port.message import MessageGateway
from ...core.port.state import StateRepository
from ...core.telemetry import LogCode, telemetry
from ...core.value.content import Payload, normalize
from ...core.value.message import Scope
from ..service.view.planner import RenderNode, ViewPlanner
from ..service.view.restorer import ViewRestorer

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
        history = await self._load_history(scope)
        cursor = self._locate(history, goal)
        target = history[cursor]
        inline = bool(scope.inline)
        tail = history[-1] if history else target
        await self._truncate(history, cursor)
        await self._status.assign(target.state)
        channel.emit(
            logging.INFO,
            LogCode.STATE_SET,
            op="set",
            state={"target": target.state},
        )
        resolved = await self._revive_payloads(target, context, inline)
        render = await self._render(scope, resolved, tail, inline)
        if render and render.changed:
            await self._apply_render(scope, render)
        else:
            await self._skip(scope, target)

    async def _load_history(self, scope: Scope) -> List[Any]:
        history = await self._ledger.recall()
        channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="set",
            history={"len": len(history)},
            scope={"chat": scope.chat, "inline": bool(scope.inline)},
        )
        return history

    def _locate(self, history: List[Any], goal: str) -> int:
        for index in range(len(history) - 1, -1, -1):
            if history[index].state == goal:
                return index
        raise StateNotFound(goal)

    async def _truncate(self, history: List[Any], cursor: int) -> None:
        trimmed = history[: cursor + 1]
        await self._ledger.archive(trimmed)
        channel.emit(
            logging.DEBUG,
            LogCode.HISTORY_SAVE,
            op="set",
            history={"len": len(trimmed)},
        )

    async def _revive_payloads(
        self,
        target,
        context: Dict[str, Any],
        inline: bool,
    ) -> List[Payload]:
        memory = await self._status.payload()
        merged = {**memory, **context}
        restored = await self._restorer.revive(target, merged, inline=inline)
        return [normalize(p) for p in restored]

    async def _render(
        self,
        scope: Scope,
        resolved: List[Payload],
        tail,
        inline: bool,
    ) -> Optional[RenderNode]:
        return await self._planner.render(
            scope,
            resolved,
            tail,
            inline=inline,
        )

    async def _apply_render(self, scope: Scope, render: RenderNode) -> None:
        current = await self._ledger.recall()
        if current:
            tail = current[-1]
            patched = self._patch_entry(tail, render)
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

    def _patch_entry(self, entry, render: RenderNode):
        limit = min(len(entry.messages), len(render.ids))
        messages = []
        for index in range(limit):
            source = entry.messages[index]
            messages.append(
                type(source)(
                    id=render.ids[index],
                    text=source.text,
                    media=source.media,
                    group=source.group,
                    markup=source.markup,
                    preview=source.preview,
                    extra=source.extra,
                    extras=render.extras[index],
                    inline=source.inline,
                    automated=source.automated,
                    ts=source.ts,
                )
            )
        messages += entry.messages[limit:]
        return type(entry)(
            state=entry.state,
            view=entry.view,
            messages=messages,
            root=entry.root,
        )

    async def _skip(self, scope: Scope, target) -> None:
        channel.emit(logging.INFO, LogCode.RENDER_SKIP, op="set")
        current = await self._ledger.recall()
        tail = current[-1] if current else target
        if tail.messages:
            await self._latest.mark(tail.messages[0].id)

from __future__ import annotations

import logging
from typing import List, Optional

from ..internal.policy import prime, validate_inline
from navigator.logging import LogCode, jlog
from ..service.view.executor import EditExecutor
from ..service.view.inline import InlineStrategy
from ..service.view.planner import RenderResult, ViewPlanner
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LatestRepository
from ...domain.service.rendering import decision
from ...domain.service.rendering.config import RenderingConfig
from ...domain.value.content import Payload, normalize
from ...domain.value.message import Scope

logger = logging.getLogger(__name__)


class Tailer:
    def __init__(
        self,
        latest: LatestRepository,
        ledger: HistoryRepository,
        planner: ViewPlanner,
        executor: EditExecutor,
        inline: InlineStrategy,
        rendering: RenderingConfig,
    ) -> None:
        self._latest = latest
        self._ledger = ledger
        self._planner = planner
        self._executor = executor
        self._inline = inline
        self._rendering = rendering

    async def peek(self) -> Optional[int]:
        marker = await self._latest.peek()
        jlog(logger, logging.INFO, LogCode.LAST_GET, message={"id": marker})
        return marker

    async def delete(self, scope: Scope) -> None:
        history = await self._ledger.recall()
        if not history:
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="last.delete", note="no_history")
            return
        if scope.inline and not scope.business:
            trimmed = history[:-1]
            await self._ledger.archive(trimmed)
            jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="last.delete", history={"len": len(trimmed)})
            marker = None
            if trimmed and trimmed[-1].messages:
                marker = int(trimmed[-1].messages[0].id)
            await self._latest.mark(marker)
            jlog(
                logger,
                logging.INFO,
                LogCode.LAST_SET if marker is not None else LogCode.LAST_DELETE,
                op="last.delete",
                message={"id": marker},
            )
            return
        tail = history[-1]
        ids: List[int] = []
        for message in tail.messages:
            ids.append(message.id)
            ids.extend(list(getattr(message, "extras", []) or []))
        if ids:
            await self._executor.delete(scope, ids)
        await self._ledger.archive(history[:-1])
        jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="last.delete", history={"len": len(history) - 1})
        await self._latest.mark(None)
        jlog(
            logger,
            logging.INFO,
            LogCode.LAST_DELETE,
            scope={"chat": scope.chat, "inline": bool(scope.inline)},
            message={"id": ids[0] if ids else None},
        )

    def _render_result(self, execution, verdict, payload) -> RenderResult:
        meta = self._executor.refine_meta(execution, verdict, payload)
        return RenderResult(
            id=execution.result.id,
            extra=list(execution.result.extra),
            meta=meta,
        )

    async def _apply(
        self,
        scope: Scope,
        verdict: decision.Decision,
        payload: Payload,
        base,
    ) -> Optional[RenderResult]:
        execution = await self._executor.execute(scope, verdict, payload, base)
        if not execution:
            return None
        return self._render_result(execution, verdict, payload)

    async def _apply_inline(
        self,
        scope: Scope,
        payload: Payload,
        head,
    ) -> Optional[RenderResult]:
        outcome = await self._inline.handle(
            scope=scope,
            payload=payload,
            tail=head,
            executor=self._executor,
            config=self._rendering,
        )
        if not outcome:
            return None
        return self._render_result(outcome.execution, outcome.decision, outcome.payload)

    async def edit(self, scope: Scope, payload: Payload) -> Optional[int]:
        marker = await self._latest.peek()
        if not marker:
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="last.edit", note="no_last_id")
            return None

        normal = normalize(payload)
        validate_inline(scope, [normal])

        history = await self._ledger.recall()
        anchor = None
        anchor_message = None
        for entry in reversed(history):
            if entry.messages and entry.messages[0].id == marker:
                anchor = entry
                anchor_message = entry.messages[0]
                break

        if anchor_message is not None:
            choice = decision.decide(anchor_message, normal, self._rendering)
        else:
            if normal.media:
                choice = decision.Decision.EDIT_MEDIA
            elif normal.text is not None:
                choice = decision.Decision.EDIT_TEXT
            elif normal.reply is not None:
                choice = decision.Decision.EDIT_MARKUP
            else:
                return None

        base = anchor if anchor is not None else prime(marker, normal)

        if scope.inline:
            head = base.messages[0] if base and base.messages else None
            result = await self._apply_inline(scope, normal, head)
        else:
            result = await self._apply(scope, choice, normal, base)

        if result:
            await self._latest.mark(result.id)
            jlog(logger, logging.INFO, LogCode.LAST_SET, op="last.edit", message={"id": result.id})

            if anchor is not None:
                cursor = None
                for index in range(len(history) - 1, -1, -1):
                    if history[index].messages and history[index].messages[0].id == marker:
                        cursor = index
                        break
                if cursor is not None:
                    from ..service.store import reindex

                    former = history[cursor].messages[0]
                    mismatch = result.id != former.id
                    bundle = [result.extra] if mismatch else None
                    patched = reindex(history[cursor], [result.id], bundle)
                    history[cursor] = patched
                    await self._ledger.archive(history)
                    jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="last.edit", history={"len": len(history)})
            return result.id

        if choice is decision.Decision.EDIT_TEXT and not (normal.text and str(normal.text).strip()):
            return None
        if choice in (decision.Decision.EDIT_MEDIA, decision.Decision.EDIT_MEDIA_CAPTION) and not (normal.media or normal.group):
            return None

        if (not scope.inline) and choice in (
            decision.Decision.EDIT_TEXT,
            decision.Decision.EDIT_MEDIA,
            decision.Decision.EDIT_MEDIA_CAPTION,
            decision.Decision.DELETE_SEND,
        ):
            targets = [marker]
            if anchor and anchor.messages:
                targets += list(anchor.messages[0].extras or [])
            await self._executor.delete(scope, targets)
            resend = await self._apply(scope, decision.Decision.RESEND, normal, None)
            if resend:
                cursor = None
                for index in range(len(history) - 1, -1, -1):
                    if history[index].messages and history[index].messages[0].id == marker:
                        cursor = index
                        break
                if cursor is not None:
                    from ..service.store import reindex

                    patched = reindex(history[cursor], [resend.id], [resend.extra])
                    history[cursor] = patched
                    await self._ledger.archive(history)
                    jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="last.edit", history={"len": len(history)})
                await self._latest.mark(resend.id)
                jlog(logger, logging.INFO, LogCode.LAST_SET, op="last.edit", message={"id": resend.id})
                return resend.id
        return None

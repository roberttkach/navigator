import logging
from typing import Optional, List

from ..internal.policy import prime, validate_inline
from ..internal.rules.inline import remap as _inline
from ..log.emit import jlog
from ..service.view.orchestrator import ViewOrchestrator
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LatestRepository
from ...domain.port.message import MessageGateway
from ...domain.service.rendering import decision
from ...domain.value.content import Payload, normalize
from ...domain.value.message import Scope
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Tailer:
    def __init__(
            self,
            latest: LatestRepository,
            ledger: HistoryRepository,
            gateway: MessageGateway,
            orchestrator: ViewOrchestrator,
    ):
        self._latest = latest
        self._ledger = ledger
        self._gateway = gateway
        self._orchestrator = orchestrator

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
            await self._gateway.delete(scope, ids)
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
            choice = decision.decide(anchor_message, normal, self._orchestrator.rendering)
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

        if scope.inline and choice == decision.Decision.DELETE_SEND:
            stem = base.messages[0] if (base and base.messages) else None
            if stem:
                mapped = _inline(stem, normal, inline=True)
                jlog(logger, logging.INFO, LogCode.INLINE_REMAP_DELETE_SEND, origin="DELETE_SEND", target=mapped.name)
                if mapped == decision.Decision.EDIT_MARKUP:
                    result = await self._orchestrator.swap(
                        scope,
                        normal.morph(media=stem.media, group=None),
                        base,
                        mapped,
                    )
                    if result:
                        await self._latest.mark(result.id)
                        jlog(logger, logging.INFO, LogCode.LAST_SET, op="last.edit", message={"id": result.id})
                        return result.id
                    jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="last.edit", note="inline_remap_markup_noop")
                    return None
                if mapped in (decision.Decision.EDIT_TEXT, decision.Decision.EDIT_MEDIA):
                    result = await self._orchestrator.swap(scope, normal, base, mapped)
                    if result:
                        await self._latest.mark(result.id)
                        jlog(logger, logging.INFO, LogCode.LAST_SET, op="last.edit", message={"id": result.id})
                        return result.id
                    jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="last.edit", note="inline_remap_noop")
                    return None
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="last.edit", note="inline_no_content_type_switch")
            return None

        if scope.inline and choice in (
                decision.Decision.EDIT_TEXT,
                decision.Decision.EDIT_MEDIA,
                decision.Decision.EDIT_MEDIA_CAPTION,
                decision.Decision.EDIT_MARKUP,
        ):
            head = base.messages[0] if base and base.messages else None
            result = await self._orchestrator.inline(scope, normal, head)
        else:
            result = await self._orchestrator.swap(scope, normal, base, choice)

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
                    mismatch = (result.id != former.id)
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
            await self._gateway.delete(scope, targets)
            resend = await self._orchestrator.swap(scope, normal, None, decision.Decision.RESEND)
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

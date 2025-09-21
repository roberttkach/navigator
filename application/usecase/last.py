import logging
from typing import Optional, List

from ..internal.policy import TailPrune, prime
from ..internal.rules.inline import remap as _inline_remap
from ..log.emit import jlog
from ..service.view.orchestrator import ViewOrchestrator
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LastMessageRepository
from ...domain.port.message import MessageGateway
from ...domain.service.rendering import decision
from ...domain.value.content import Payload, normalize
from ...domain.value.message import Scope
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Tailer:
    def __init__(
            self,
            last_repo: LastMessageRepository,
            history_repo: HistoryRepository,
            gateway: MessageGateway,
            orchestrator: ViewOrchestrator,
    ):
        self._last_repo = last_repo
        self._history_repo = history_repo
        self._gateway = gateway
        self._orchestrator = orchestrator

    async def get_id(self) -> Optional[int]:
        mid = await self._last_repo.get_last_id()
        jlog(logger, logging.INFO, LogCode.LAST_GET, message={"id": mid})
        return mid

    async def delete(self, scope: Scope) -> None:
        history = await self._history_repo.get_history()
        if not history:
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="last.delete", note="no_history")
            return
        if scope.inline and not scope.business:
            if TailPrune:
                new_history = history[:-1]
                await self._history_repo.save_history(new_history)
                jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="last.delete", history={"len": len(new_history)})
                new_last_id = None
                if new_history and new_history[-1].messages:
                    new_last_id = int(new_history[-1].messages[0].id)
                await self._last_repo.set_last_id(new_last_id)
                jlog(
                    logger,
                    logging.INFO,
                    LogCode.LAST_SET if new_last_id is not None else LogCode.LAST_DELETE,
                    op="last.delete",
                    message={"id": new_last_id},
                )
            else:
                jlog(
                    logger,
                    logging.INFO,
                    LogCode.RENDER_SKIP,
                    op="last.delete",
                    scope={"chat": scope.chat, "inline": True},
                    note="inline_noop",
                )
            return
        last_node = history[-1]
        ids: List[int] = []
        for m in last_node.messages:
            ids.append(m.id)
            ids.extend(list(getattr(m, "extras", []) or []))
        if ids:
            await self._gateway.delete(scope, ids)
        await self._history_repo.save_history(history[:-1])
        jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="last.delete", history={"len": len(history) - 1})
        await self._last_repo.set_last_id(None)
        jlog(
            logger,
            logging.INFO,
            LogCode.LAST_DELETE,
            scope={"chat": scope.chat, "inline": bool(scope.inline)},
            message={"id": ids[0] if ids else None},
        )

    async def edit(self, scope: Scope, payload: Payload) -> Optional[int]:
        last_id = await self._last_repo.get_last_id()
        if not last_id:
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="last.edit", note="no_last_id")
            return None

        p = normalize(payload)
        if scope.inline and getattr(p, "group", None):
            first = p.group[0]
            p = p.morph(media=first, group=None)

        history = await self._history_repo.get_history()
        last_entry = None
        for e in reversed(history):
            if e.messages and e.messages[0].id == last_id:
                last_entry = e
                break

        if last_entry is not None:
            dec = decision.decide(last_entry, p, self._orchestrator.rendering_config)
        else:
            if p.media:
                dec = decision.Decision.EDIT_MEDIA
            elif p.text is not None:
                dec = decision.Decision.EDIT_TEXT
            elif p.reply is not None:
                dec = decision.Decision.EDIT_MARKUP
            else:
                return None

        base = last_entry if last_entry is not None else prime(last_id, p)

        if scope.inline and dec == decision.Decision.DELETE_SEND:
            base_msg = base.messages[0] if (base and base.messages) else None
            if base_msg:
                remapped = _inline_remap(base_msg, p, inline=True)
                jlog(logger, logging.INFO, LogCode.INLINE_REMAP_DELETE_SEND, from_="DELETE_SEND", to_=remapped.name)
                if remapped == decision.Decision.EDIT_MARKUP:
                    result = await self._orchestrator.swap(scope, p.morph(media=base_msg.media, group=None), base,
                                                           remapped)
                    if result:
                        await self._last_repo.set_last_id(result.id)
                        jlog(logger, logging.INFO, LogCode.LAST_SET, op="last.edit", message={"id": result.id})
                        return result.id
                    jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="last.edit", note="inline_remap_markup_noop")
                    return None
                if remapped in (decision.Decision.EDIT_TEXT, decision.Decision.EDIT_MEDIA):
                    result = await self._orchestrator.swap(scope, p, base, remapped)
                    if result:
                        await self._last_repo.set_last_id(result.id)
                        jlog(logger, logging.INFO, LogCode.LAST_SET, op="last.edit", message={"id": result.id})
                        return result.id
                    jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="last.edit", note="inline_remap_noop")
                    return None
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="last.edit", note="inline_no_content_type_switch")
            return None

        if scope.inline and dec in (
                decision.Decision.EDIT_TEXT,
                decision.Decision.EDIT_MEDIA,
                decision.Decision.EDIT_MEDIA_CAPTION,
                decision.Decision.EDIT_MARKUP,
        ):
            lm = base.messages[0] if base and base.messages else None
            result = await self._orchestrator._inline.handle_element(
                scope=scope,
                payload=p,
                last_message=lm,
                inline=True,
                swap=self._orchestrator.swap,
                rendering_config=self._orchestrator.rendering_config,
            )
        else:
            result = await self._orchestrator.swap(scope, p, base, dec)

        if result:
            await self._last_repo.set_last_id(result.id)
            jlog(logger, logging.INFO, LogCode.LAST_SET, op="last.edit", message={"id": result.id})

            if last_entry is not None:
                idx = None
                for i in range(len(history) - 1, -1, -1):
                    if history[i].messages and history[i].messages[0].id == last_id:
                        idx = i
                        break
                if idx is not None:
                    from ..service.store import reindex
                    old_msg = history[idx].messages[0]
                    need_patch = (result.id != old_msg.id)
                    new_extras = [result.extra] if need_patch else None
                    patched = reindex(history[idx], [result.id], new_extras)
                    history[idx] = patched
                    await self._history_repo.save_history(history)
                    jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="last.edit", history={"len": len(history)})
            return result.id

        if dec is decision.Decision.EDIT_TEXT and not (p.text and str(p.text).strip()):
            return None
        if dec in (decision.Decision.EDIT_MEDIA, decision.Decision.EDIT_MEDIA_CAPTION) and not (p.media or p.group):
            return None

        if (not scope.inline) and dec in (
                decision.Decision.EDIT_TEXT,
                decision.Decision.EDIT_MEDIA,
                decision.Decision.EDIT_MEDIA_CAPTION,
                decision.Decision.DELETE_SEND,
        ):
            ids_to_del = [last_id]
            if last_entry and last_entry.messages:
                ids_to_del += list(last_entry.messages[0].extras or [])
            await self._gateway.delete(scope, ids_to_del)
            resend_result = await self._orchestrator.swap(scope, p, None, decision.Decision.RESEND)
            if resend_result:
                idx = None
                for i in range(len(history) - 1, -1, -1):
                    if history[i].messages and history[i].messages[0].id == last_id:
                        idx = i
                        break
                if idx is not None:
                    from ..service.store import reindex
                    patched = reindex(history[idx], [resend_result.id], [resend_result.extra])
                    history[idx] = patched
                    await self._history_repo.save_history(history)
                    jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="last.edit", history={"len": len(history)})
                await self._last_repo.set_last_id(resend_result.id)
                jlog(logger, logging.INFO, LogCode.LAST_SET, op="last.edit", message={"id": resend_result.id})
                return resend_result.id
        return None

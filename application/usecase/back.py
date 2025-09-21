import logging
from typing import Dict, Any

from ..log.decorators import log_io
from ..log.emit import jlog
from ..service.view.orchestrator import ViewOrchestrator
from ..service.view.restorer import ViewRestorer
from ...domain.error import HistoryEmpty
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LastMessageRepository
from ...domain.port.message import MessageGateway
from ...domain.port.state import StateRepository
from ...domain.value.content import normalize
from ...domain.value.message import Scope
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Rewinder:
    def __init__(
            self,
            history_repo: HistoryRepository,
            state_repo: StateRepository,
            gateway: MessageGateway,
            restorer: ViewRestorer,
            orchestrator: ViewOrchestrator,
            last_repo: LastMessageRepository,
    ):
        self._history_repo = history_repo
        self._state_repo = state_repo
        self._gateway = gateway
        self._restorer = restorer
        self._orchestrator = orchestrator
        self._last_repo = last_repo

    @log_io(None, None, None)
    async def execute(self, scope: Scope, handler_data: Dict[str, Any]) -> None:
        history = await self._history_repo.get_history()
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
        entry_from = history[-1]
        entry_to = history[-2]
        is_inline = bool(scope.inline)
        fsm_data: Dict[str, Any] = await self._state_repo.get_data()
        merged_handler_data = {**fsm_data, **handler_data}
        restored_payloads = await self._restorer.restore_node(entry_to, merged_handler_data, inline=is_inline)
        resolved_payloads = [normalize(p) for p in restored_payloads]
        if not is_inline:
            render_result = await self._orchestrator.render_node(
                "back",
                scope,
                resolved_payloads,
                entry_from,
                inline=False,
            )
        else:
            render_result = await self._orchestrator.render_node(
                "back",
                scope,
                resolved_payloads,
                entry_from,
                inline=True,
            )

        # Политика хвоста: удаление при inline и наличии business.
        from ..internal import policy as _pol
        if is_inline and _pol.TailMode in ("delete", "collapse") and getattr(scope, "business", None):
            to_delete = []
            for m in entry_from.messages[1:]:
                to_delete.append(m.id)
                to_delete.extend(list(getattr(m, "extras", []) or []))
            if to_delete:
                first_n = to_delete[:20]
                jlog(
                    logger,
                    logging.DEBUG,
                    LogCode.INLINE_TAIL_DELETE_IDS,
                    ids=first_n,
                    total=len(to_delete),
                )
                await self._gateway.delete(scope, to_delete)

        if not render_result or not render_result.changed:
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="back")
            await self._state_repo.set_state(entry_to.state)
            if entry_to.messages:
                mid = entry_to.messages[0].id
                await self._last_repo.set_last_id(mid)
            history_updated = history[:-1]
            await self._history_repo.save_history(history_updated)
            jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="back", history={"len": len(history_updated)})
            return
        patched_len = min(len(entry_to.messages), len(render_result.ids))
        patched_msgs = [
            type(entry_to.messages[i])(
                id=render_result.ids[i],
                text=entry_to.messages[i].text,
                media=entry_to.messages[i].media,
                group=entry_to.messages[i].group,
                markup=entry_to.messages[i].markup,
                preview=entry_to.messages[i].preview,
                extra=entry_to.messages[i].extra,
                extras=render_result.extras[i],
                inline=entry_to.messages[i].inline,
                automated=entry_to.messages[i].automated,
                ts=entry_to.messages[i].ts,
            )
            for i in range(patched_len)
        ]
        new_msgs = patched_msgs + entry_to.messages[patched_len:]
        patched_to = type(entry_to)(
            state=entry_to.state,
            view=entry_to.view,
            messages=new_msgs,
            root=entry_to.root,
        )
        history_updated = history[:-1]
        history_updated[-1] = patched_to
        await self._history_repo.save_history(history_updated)
        jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="back", history={"len": len(history_updated)})
        await self._state_repo.set_state(entry_to.state)
        jlog(logger, logging.INFO, LogCode.STATE_SET, op="back", state={"target": entry_to.state})
        await self._last_repo.set_last_id(render_result.ids[0])
        jlog(logger, logging.INFO, LogCode.LAST_SET, op="back", message={"id": render_result.ids[0]})

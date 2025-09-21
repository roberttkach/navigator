import logging
from typing import Dict, Any, Optional

from ..log.decorators import log_io
from ..log.emit import jlog
from ..service.view.orchestrator import ViewOrchestrator
from ..service.view.restorer import ViewRestorer
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LastMessageRepository
from ...domain.port.message import MessageGateway
from ...domain.port.state import StateRepository
from ...domain.value.content import normalize
from ...domain.value.message import Scope
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Setter:
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
    async def execute(
            self,
            scope: Scope,
            target_state: str,
            handler_data: Dict[str, Any],
    ) -> None:
        history = await self._history_repo.get_history()
        jlog(
            logger,
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="set",
            history={"len": len(history)},
            scope={"chat": scope.chat, "inline": bool(scope.inline)},
        )
        target_idx: Optional[int] = None
        for i in range(len(history) - 1, -1, -1):
            if history[i].state == target_state:
                target_idx = i
                break
        if target_idx is None:
            await self._gateway.alert(scope)
            jlog(
                logger,
                logging.INFO,
                LogCode.GATEWAY_NOTIFY_EMPTY,
                op="set",
                scope={"chat": scope.chat, "inline": bool(scope.inline)},
            )
            return
        target_entry = history[target_idx]
        is_inline = bool(scope.inline)
        current_tail = history[-1]
        new_history = history[: target_idx + 1]
        await self._history_repo.save_history(new_history)
        jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="set", history={"len": len(new_history)})
        await self._state_repo.set_state(target_entry.state)
        jlog(logger, logging.INFO, LogCode.STATE_SET, op="set", state={"target": target_entry.state})
        fsm_data = await self._state_repo.get_data()
        merged_handler_data = {**fsm_data, **handler_data}
        restored_payloads = await self._restorer.restore_node(target_entry, merged_handler_data, inline=is_inline)
        resolved_payloads = [normalize(p) for p in restored_payloads]
        if not is_inline:
            render_result = await self._orchestrator.render_node(
                "set",
                scope,
                resolved_payloads,
                current_tail,
                inline=False,
            )
        else:
            render_result = await self._orchestrator.render_node(
                "set",
                scope,
                resolved_payloads,
                current_tail,
                inline=True,
            )
        if render_result and render_result.changed:
            # Политика хвоста: удаление при inline и наличии business.
            from ..internal import policy as _pol
            if is_inline and _pol.TailMode in ("delete", "collapse") and getattr(scope, "business", None):
                to_delete = []
                for m in current_tail.messages[1:]:
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

            current_history = await self._history_repo.get_history()
            if current_history:
                tail = current_history[-1]
                patched_tail = type(tail)(
                    state=tail.state,
                    view=tail.view,
                    messages=[
                                 type(tail.messages[i])(
                                     id=render_result.ids[i],
                                     text=tail.messages[i].text,
                                     media=tail.messages[i].media,
                                     group=tail.messages[i].group,
                                     markup=tail.messages[i].markup,
                                     preview=tail.messages[i].preview,
                                     extra=tail.messages[i].extra,
                                     extras=render_result.extras[i],
                                     inline=tail.messages[i].inline,
                                     automated=tail.messages[i].automated,
                                     ts=tail.messages[i].ts,
                                 )
                                 for i in range(min(len(tail.messages), len(render_result.ids)))
                             ]
                             + tail.messages[min(len(tail.messages), len(render_result.ids)):],
                    root=tail.root,
                )
                await self._history_repo.save_history(current_history[:-1] + [patched_tail])
                jlog(logger, logging.DEBUG, LogCode.HISTORY_SAVE, op="set", history={"len": len(current_history)})
            await self._last_repo.set_last_id(render_result.ids[0])
            jlog(logger, logging.INFO, LogCode.LAST_SET, op="set", message={"id": render_result.ids[0]})
        else:
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="set")
            current = await self._history_repo.get_history()
            tail = current[-1] if current else target_entry
            if tail.messages:
                await self._last_repo.set_last_id(tail.messages[0].id)
            return

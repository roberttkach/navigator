import logging
from typing import Optional, List

from ..log.decorators import log_io
from ..log.emit import jlog
from ..map.entry import EntryMapper, NodeResult
from ..service.view.orchestrator import ViewOrchestrator
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LastMessageRepository
from ...domain.port.state import StateRepository
from ...domain.service.history import policy as history_policy
from ...domain.service.scope import scope_kv
from ...domain.value.content import Payload, resolve_content
from ...domain.value.message import Scope
from ...logging.code import LogCode

logger = logging.getLogger(__name__)


class AddUseCase:
    def __init__(
            self,
            history_repo: HistoryRepository,
            state_repo: StateRepository,
            last_repo: LastMessageRepository,
            orchestrator: ViewOrchestrator,
            mapper: EntryMapper,
            history_limit: int,
    ):
        self._history_repo = history_repo
        self._state_repo = state_repo
        self._last_repo = last_repo
        self._orchestrator = orchestrator
        self._mapper = mapper
        self._history_limit = history_limit

    @log_io(None, None, None)
    async def execute(
            self,
            scope: Scope,
            payloads: List[Payload],
            view: Optional[str],
            root: bool = False,
    ) -> None:
        resolved = [resolve_content(p) for p in payloads]
        history = await self._history_repo.get_history()
        jlog(
            logger,
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="add",
            history={"len": len(history)},
            scope=scope_kv(scope),
        )
        last_entry = history[-1] if history else None
        rr = await self._orchestrator.render_node("add", scope, resolved, last_entry, inline=bool(scope.inline_id))
        if not rr or not rr.ids or not rr.changed:
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="add")
            return
        current_state = await self._state_repo.get_state()
        jlog(logger, logging.INFO, LogCode.STATE_GET, op="add", state={"current": current_state})

        effective_payloads = resolved[:len(rr.ids)]
        new_entry = self._mapper.from_node_result(
            NodeResult(rr.ids, rr.extras, rr.metas),
            effective_payloads,
            current_state,
            view,
            root,
            base=None,
        )

        new_history = [new_entry] if root else (history + [new_entry])
        from ..service.ops import save_history_and_last
        await save_history_and_last(
            self._history_repo, self._last_repo, history_policy, self._history_limit, new_history, op="add"
        )

import logging
from typing import List

from ..log.decorators import log_io
from ..log.emit import jlog
from ..map.entry import EntryMapper, NodeResult
from ..service.view.orchestrator import ViewOrchestrator
from ..service.view.policy import payload_with_allowed_reply
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LastMessageRepository
from ...domain.port.state import StateRepository
from ...domain.service.history import policy as history_policy
from ...domain.value.content import Payload, normalize
from ...domain.value.message import Scope
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Swapper:
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
    async def execute(self, scope: Scope, payloads: List[Payload]) -> None:
        resolved = [payload_with_allowed_reply(scope, normalize(p)) for p in payloads]
        history = await self._history_repo.get_history()
        jlog(logger, logging.DEBUG, LogCode.HISTORY_LOAD, op="replace", history={"len": len(history)})
        last_entry = history[-1] if history else None
        rr = await self._orchestrator.render_node(
            "replace", scope, resolved, last_entry, inline=bool(scope.inline)
        )
        if not rr or not rr.ids or not rr.changed:
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="replace")
            return
        current_state = await self._state_repo.get_state()

        effective_payloads = resolved[:len(rr.ids)]
        new_entry = self._mapper.convert(
            NodeResult(rr.ids, rr.extras, rr.metas),
            effective_payloads,
            current_state,
            last_entry.view if last_entry else None,
            root=bool(last_entry.root) if last_entry else False,
            base=last_entry,
        )
        if not history:
            updated = [new_entry]
        else:
            updated = history[:-1] + [new_entry]
        from ..service.store import persist
        await persist(
            self._history_repo, self._last_repo, history_policy, self._history_limit, updated, op="replace"
        )

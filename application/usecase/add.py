import logging
from typing import Optional, List

from ..log.decorators import trace
from ..log.emit import jlog
from ..map.entry import EntryMapper, Outcome
from ..service.view.orchestrator import ViewOrchestrator
from ..service.view.policy import adapt
from ...domain.port.history import HistoryRepository
from ...domain.port.last import LatestRepository
from ...domain.port.state import StateRepository
from ...domain.service.history import policy as chronicle
from ...domain.service.scope import profile
from ...domain.value.content import Payload, normalize
from ...domain.value.message import Scope
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class Appender:
    def __init__(
            self,
            archive: HistoryRepository,
            state: StateRepository,
            tail: LatestRepository,
            orchestrator: ViewOrchestrator,
            mapper: EntryMapper,
            limit: int,
    ):
        self._archive = archive
        self._state = state
        self._tail = tail
        self._orchestrator = orchestrator
        self._mapper = mapper
        self._limit = limit

    @trace(None, None, None)
    async def execute(
            self,
            scope: Scope,
            bundle: List[Payload],
            view: Optional[str],
            root: bool = False,
    ) -> None:
        adjusted = [adapt(scope, normalize(p)) for p in bundle]
        records = await self._archive.recall()
        jlog(
            logger,
            logging.DEBUG,
            LogCode.HISTORY_LOAD,
            op="add",
            history={"len": len(records)},
            scope=profile(scope),
        )
        trail = records[-1] if records else None
        render = await self._orchestrator.render("add", scope, adjusted, trail, inline=bool(scope.inline))
        if not render or not render.ids or not render.changed:
            jlog(logger, logging.INFO, LogCode.RENDER_SKIP, op="add")
            return
        status = await self._state.status()
        jlog(logger, logging.INFO, LogCode.STATE_GET, op="add", state={"current": status})

        usable = adjusted[:len(render.ids)]
        entry = self._mapper.convert(
            Outcome(render.ids, render.extras, render.metas),
            usable,
            status,
            view,
            root,
            base=None,
        )

        timeline = [entry] if root else (records + [entry])
        from ..service.store import persist
        await persist(
            self._archive, self._tail, chronicle, self._limit, timeline, op="add"
        )

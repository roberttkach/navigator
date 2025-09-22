import logging
from typing import Optional, Dict, Any

from aiogram.fsm.context import FSMContext

from .keys import FSM_GRAPH_NODES_KEY, FSM_GRAPH_EDGES_KEY
from ...domain.entity.stategraph import Graph
from ...domain.log.emit import jlog
from ...domain.port.state import StateRepository
from ...domain.log.code import LogCode

logger = logging.getLogger(__name__)


class StateRepo(StateRepository):
    def __init__(self, state: FSMContext):
        self._state = state

    async def status(self) -> Optional[str]:
        s = await self._state.get_state()
        jlog(logger, logging.DEBUG, LogCode.STATE_GET, state={"current": s})
        return s

    async def assign(self, state: Optional[str]) -> None:
        await self._state.set_state(state)
        jlog(logger, logging.DEBUG, LogCode.STATE_SET, state={"target": state})

    async def diagram(self) -> Graph:
        data = await self._state.get_data()
        nodes = data.get(FSM_GRAPH_NODES_KEY, [])
        edges = data.get(FSM_GRAPH_EDGES_KEY, {})
        jlog(logger, logging.DEBUG, LogCode.GRAPH_GET, graph={"nodes_len": len(nodes), "edges_keys": len(edges)})
        return Graph(
            nodes=nodes,
            edges=edges,
        )

    async def capture(self, graph: Graph) -> None:
        await self._state.update_data({
            FSM_GRAPH_NODES_KEY: graph.nodes,
            FSM_GRAPH_EDGES_KEY: graph.edges,
        })
        jlog(logger, logging.DEBUG, LogCode.GRAPH_SAVE,
             graph={"nodes_len": len(graph.nodes), "edges_keys": len(graph.edges)})

    async def payload(self) -> Dict[str, Any]:
        d = await self._state.get_data()
        filtered = {k: v for k, v in d.items() if not str(k).startswith("nav")}
        count = len(filtered)
        jlog(logger, logging.DEBUG, LogCode.STATE_DATA_GET, data={"keys": count})
        return filtered


__all__ = ["StateRepo"]

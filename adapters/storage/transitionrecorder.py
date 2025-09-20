import logging
from typing import Optional, Set, Dict, List

from ...domain.entity.stategraph import Graph
from ...domain.log.emit import jlog
from ...domain.port.state import StateRepository
from ...domain.port.transition import TransitionObserver
from ...domain.log.code import LogCode


class TransitionRecorder(TransitionObserver):
    def __init__(self, state_repo: StateRepository):
        self._state_repo = state_repo
        self._logger = logging.getLogger(__name__)

    async def on_transition(self, from_state: Optional[str], to_state: str) -> None:
        graph = await self._state_repo.get_graph()
        nodes_before = list(graph.nodes)
        before_edges_raw: Dict[str, List[str]] = dict(graph.edges)
        if from_state is None:
            nodes: Set[str] = set(graph.nodes)
            nodes.add(to_state)
            new_graph = Graph(
                nodes=sorted(list(nodes)),
                edges={k: list(v) for k, v in graph.edges.items()},
            )
            await self._state_repo.save_graph(new_graph)
            jlog(
                self._logger,
                logging.DEBUG,
                LogCode.TRANSITION,
                state={"from": None, "to": to_state},
                nodes_before=len(nodes_before),
                nodes_after=len(new_graph.nodes),
                edges_added=[],
            )
            return
        if from_state == to_state:
            return
        nodes: Set[str] = set(graph.nodes)
        nodes.update({from_state, to_state})
        edges_sets: Dict[str, Set[str]] = {st: set(neigh) for st, neigh in graph.edges.items()}
        edges_sets.setdefault(from_state, set()).add(to_state)
        edges_sets.setdefault(to_state, set()).add(from_state)
        updated_edges: Dict[str, List[str]] = {st: sorted(list(neigh)) for st, neigh in edges_sets.items()}
        new_graph = Graph(nodes=sorted(list(nodes)), edges=updated_edges)
        await self._state_repo.save_graph(new_graph)
        before_edges: Dict[str, Set[str]] = {st: set(neigh) for st, neigh in before_edges_raw.items()}
        after_edges: Dict[str, Set[str]] = {st: set(neigh) for st, neigh in new_graph.edges.items()}
        added_from = sorted(list(after_edges.get(from_state, set()) - before_edges.get(from_state, set())))
        added_to = sorted(list(after_edges.get(to_state, set()) - before_edges.get(to_state, set())))
        jlog(
            self._logger,
            logging.DEBUG,
            LogCode.TRANSITION,
            state={"from": from_state, "to": to_state},
            nodes_before=len(nodes_before),
            nodes_after=len(new_graph.nodes),
            edges_added={"from": added_from, "to": added_to},
        )


__all__ = ["TransitionRecorder"]

import logging
from typing import Optional, Set, Dict, List

from ...domain.entity.stategraph import Graph
from ...domain.log.emit import jlog
from ...domain.port.state import StateRepository
from ...domain.port.transition import TransitionObserver
from ...domain.log.code import LogCode


class TransitionRecorder(TransitionObserver):
    def __init__(self, status: StateRepository):
        self._status = status
        self._logger = logging.getLogger(__name__)

    async def on_transition(self, origin: Optional[str], target: str) -> None:
        chart = await self._status.diagram()
        baseline = list(chart.nodes)
        prior: Dict[str, Set[str]] = {name: set(paths) for name, paths in chart.edges.items()}
        if origin is None:
            nodes: Set[str] = set(chart.nodes)
            nodes.add(target)
            fresh = Graph(
                nodes=sorted(list(nodes)),
                edges={name: list(paths) for name, paths in chart.edges.items()},
            )
            await self._status.capture(fresh)
            jlog(
                self._logger,
                logging.DEBUG,
                LogCode.TRANSITION,
                state={"from": None, "to": target},
                nodes_before=len(baseline),
                nodes_after=len(fresh.nodes),
                edges_added=[],
            )
            return
        if origin == target:
            return
        nodes: Set[str] = set(chart.nodes)
        nodes.update({origin, target})
        bundles: Dict[str, Set[str]] = {name: set(paths) for name, paths in chart.edges.items()}
        bundles.setdefault(origin, set()).add(target)
        bundles.setdefault(target, set()).add(origin)
        edges: Dict[str, List[str]] = {name: sorted(list(paths)) for name, paths in bundles.items()}
        fresh = Graph(nodes=sorted(list(nodes)), edges=edges)
        await self._status.capture(fresh)
        after: Dict[str, Set[str]] = {name: set(paths) for name, paths in fresh.edges.items()}
        origin_added = sorted(list(after.get(origin, set()) - prior.get(origin, set())))
        target_added = sorted(list(after.get(target, set()) - prior.get(target, set())))
        jlog(
            self._logger,
            logging.DEBUG,
            LogCode.TRANSITION,
            state={"from": origin, "to": target},
            nodes_before=len(baseline),
            nodes_after=len(fresh.nodes),
            edges_added={"from": origin_added, "to": target_added},
        )


__all__ = ["TransitionRecorder"]

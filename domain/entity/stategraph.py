from dataclasses import dataclass, field
from typing import List, Dict


@dataclass(frozen=True, slots=True)
class Graph:
    nodes: List[str] = field(default_factory=list)
    edges: Dict[str, List[str]] = field(default_factory=dict)

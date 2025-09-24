from dataclasses import dataclass
from typing import Any, Dict


@dataclass(frozen=True, slots=True)
class Markup:
    kind: str
    data: Dict[str, Any]

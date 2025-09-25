from typing import Dict, Any

from ..value.message import Scope


def profile(s: Scope) -> Dict[str, Any]:
    data: Dict[str, Any] = {
        "chat": s.chat,
        "inline": bool(s.inline),
        "category": s.category,
        "direct": bool(getattr(s, "direct", False)),
    }
    if s.topic is not None:
        data["topic"] = s.topic
    return data

import warnings
from typing import Dict, Any

from ..value.message import Scope


def profile(s: Scope) -> Dict[str, Any]:
    data: Dict[str, Any] = {"chat": s.chat, "inline": bool(s.inline), "category": s.category}
    if s.direct_topic_id is not None:
        data["direct_topic_id"] = s.direct_topic_id
    return data


def scope_kv(s: Scope) -> Dict[str, Any]:
    warnings.warn("scope_kv is deprecated; use profile", DeprecationWarning, stacklevel=2)
    return profile(s)

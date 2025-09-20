import warnings
from typing import Dict, Any

from ..value.message import Scope


def profile(s: Scope) -> Dict[str, Any]:
    return {"chat": s.chat, "inline": bool(s.inline), "category": s.category}


def scope_kv(s: Scope) -> Dict[str, Any]:
    warnings.warn("scope_kv is deprecated; use profile", DeprecationWarning, stacklevel=2)
    return profile(s)

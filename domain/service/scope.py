from typing import Dict, Any

from ..value.message import Scope


def scope_kv(s: Scope) -> Dict[str, Any]:
    return {"chat": s.chat, "inline": bool(s.inline_id), "chat_kind": s.chat_kind}

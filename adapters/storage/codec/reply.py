from __future__ import annotations

from typing import Any, Dict, Optional

from navigator.core.entity.markup import Markup


class ReplyCodec:
    @staticmethod
    def pack(rm: Optional[Markup]) -> Optional[Dict[str, Any]]:
        if not rm:
            return None
        return {"kind": rm.kind, "data": rm.data}

    @staticmethod
    def unpack(data: Any) -> Optional[Markup]:
        if not isinstance(data, Dict):
            return None
        kind = data.get("kind")
        payload = data.get("data")
        if isinstance(kind, str) and isinstance(payload, dict):
            return Markup(kind=kind, data=payload)
        return None


__all__ = ["ReplyCodec"]

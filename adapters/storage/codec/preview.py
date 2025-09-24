from __future__ import annotations

from typing import Any, Dict, Optional

from navigator.domain.value.content import Preview


class PreviewCodec:
    @staticmethod
    def pack(p: Optional[Preview]) -> Optional[Dict[str, Any]]:
        if not p:
            return None
        return {
            "url": p.url,
            "small": p.small,
            "large": p.large,
            "above": p.above,
            "disabled": p.disabled,
        }

    @staticmethod
    def unpack(p: Any) -> Optional[Preview]:
        if not isinstance(p, Dict):
            return None
        return Preview(
            url=p.get("url"),
            small=bool(p.get("small", False)),
            large=bool(p.get("large", False)),
            above=bool(p.get("above", False)),
            disabled=p.get("disabled"),
        )


__all__ = ["PreviewCodec"]

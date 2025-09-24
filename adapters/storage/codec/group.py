from __future__ import annotations

from typing import Any, Dict, List, Optional

from navigator.core.entity.media import MediaItem

from .media import MediaCodec


class GroupCodec:
    @staticmethod
    def pack(items: Optional[List[MediaItem]]) -> Optional[List[Dict[str, Any]]]:
        if not items:
            return None
        packed: List[Dict[str, Any]] = []
        for item in items:
            encoded = MediaCodec.pack(item)
            if encoded is not None:
                packed.append(encoded)
        return packed or None

    @staticmethod
    def unpack(items: Any) -> Optional[List[MediaItem]]:
        if not isinstance(items, list):
            return None
        out: List[MediaItem] = []
        for raw in items:
            media = MediaCodec.unpack(raw)
            if media is not None:
                out.append(media)
        return out or None


__all__ = ["GroupCodec"]

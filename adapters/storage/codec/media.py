from __future__ import annotations

from typing import Any, Dict, Optional

from navigator.domain.entity.media import MediaItem, MediaType


class MediaCodec:
    @staticmethod
    def pack(item: Optional[MediaItem]) -> Optional[Dict[str, Any]]:
        if not item:
            return None
        return {
            "type": item.type.value,
            "file": item.path,
            "caption": item.caption,
        }

    @staticmethod
    def unpack(data: Any) -> Optional[MediaItem]:
        if not isinstance(data, Dict):
            return None
        kind = data.get("type")
        identifier = data.get("file")
        if not (isinstance(kind, str) and isinstance(identifier, str) and identifier):
            return None
        return MediaItem(type=MediaType(kind), path=identifier, caption=data.get("caption"))


__all__ = ["MediaCodec"]

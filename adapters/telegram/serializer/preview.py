from __future__ import annotations

from typing import Any, Optional

from aiogram.types import LinkPreviewOptions

from navigator.domain.port.preview import LinkPreviewCodec
from navigator.domain.value.content import Preview


class TelegramLinkPreviewCodec(LinkPreviewCodec):
    def encode(self, preview: Preview) -> LinkPreviewOptions:
        payload = {
            "url": preview.url,
            "prefer_small_media": bool(preview.small),
            "prefer_large_media": bool(preview.large),
            "show_above_text": bool(preview.above),
        }
        if preview.disabled is not None:
            payload["is_disabled"] = bool(preview.disabled)
        return LinkPreviewOptions(**payload)

    def decode(self, data: Any) -> Optional[Preview]:
        if data is None:
            return None
        if isinstance(data, Preview):
            return data
        if isinstance(data, LinkPreviewOptions):
            return Preview(
                url=getattr(data, "url", None),
                small=bool(getattr(data, "prefer_small_media", False)),
                large=bool(getattr(data, "prefer_large_media", False)),
                above=bool(getattr(data, "show_above_text", False)),
                disabled=getattr(data, "is_disabled", None),
            )
        if isinstance(data, dict):
            return Preview(
                url=data.get("url"),
                small=bool(data.get("prefer_small_media", data.get("small", False))),
                large=bool(data.get("prefer_large_media", data.get("large", False))),
                above=bool(data.get("show_above_text", data.get("above", False))),
                disabled=data.get("is_disabled", data.get("disabled")),
            )
        return None


__all__ = ["TelegramLinkPreviewCodec"]


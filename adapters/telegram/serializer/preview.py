from __future__ import annotations

from typing import Any, Optional

from aiogram.client.default import Default
from aiogram.types import LinkPreviewOptions

from navigator.core.port.preview import LinkPreviewCodec
from navigator.core.value.content import Preview


class TelegramLinkPreviewCodec(LinkPreviewCodec):
    @staticmethod
    def _flag(value: Any) -> bool:
        if isinstance(value, Default):
            return False
        return bool(value)

    @staticmethod
    def _maybe(value: Any) -> Optional[bool]:
        if isinstance(value, Default) or value is None:
            return None
        return bool(value)

    def encode(self, preview: Preview) -> LinkPreviewOptions:
        payload = {
            "prefer_small_media": bool(preview.small),
            "prefer_large_media": bool(preview.large),
            "show_above_text": bool(preview.above),
        }
        if preview.url is not None:
            payload["url"] = preview.url
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
                small=self._flag(getattr(data, "prefer_small_media", False)),
                large=self._flag(getattr(data, "prefer_large_media", False)),
                above=self._flag(getattr(data, "show_above_text", False)),
                disabled=self._maybe(getattr(data, "is_disabled", None)),
            )
        if isinstance(data, dict):
            return Preview(
                url=data.get("url"),
                small=self._flag(data.get("prefer_small_media", data.get("small", False))),
                large=self._flag(data.get("prefer_large_media", data.get("large", False))),
                above=self._flag(data.get("show_above_text", data.get("above", False))),
                disabled=self._maybe(data.get("is_disabled", data.get("disabled"))),
            )
        return None


__all__ = ["TelegramLinkPreviewCodec"]


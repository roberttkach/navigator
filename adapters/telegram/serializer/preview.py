from __future__ import annotations

from typing import Optional

from aiogram.types import LinkPreviewOptions

from domain.value.content import Preview


def to_options(preview: Preview | None) -> Optional[LinkPreviewOptions]:
    if preview is None:
        return None
    if isinstance(preview, Preview):
        return LinkPreviewOptions(
            url=preview.url,
            prefer_small_media=preview.small,
            prefer_large_media=preview.large,
            show_above_text=preview.above,
            is_disabled=preview.disabled,
        )
    return None


__all__ = ["to_options"]

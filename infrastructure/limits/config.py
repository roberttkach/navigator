from __future__ import annotations

from navigator.domain.port.limits import Limits


class ConfigLimits(Limits):
    def __init__(
        self,
        *,
        text: int,
        caption: int,
        floor: int,
        ceiling: int,
        blend: set[str],
    ) -> None:
        self._text = int(text)
        self._caption = int(caption)
        self._floor = int(floor)
        self._ceiling = int(ceiling)
        self._blend = set(blend)

    def text_max(self) -> int:
        return self._text

    def caption_max(self) -> int:
        return self._caption

    def album_floor(self) -> int:
        return self._floor

    def album_ceiling(self) -> int:
        return self._ceiling

    def album_blend(self) -> set[str]:
        return set(self._blend)


__all__ = ["ConfigLimits"]

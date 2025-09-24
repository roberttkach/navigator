from __future__ import annotations

from navigator.core.port.limits import Limits


class ConfigLimits(Limits):
    def __init__(
        self,
        *,
        text: int,
        caption: int,
        minimum: int,
        maximum: int,
        mix: set[str],
    ) -> None:
        self._text = int(text)
        self._caption = int(caption)
        self._minimum = int(minimum)
        self._maximum = int(maximum)
        self._mix = set(mix)

    def textlimit(self) -> int:
        return self._text

    def captionlimit(self) -> int:
        return self._caption

    def groupmin(self) -> int:
        return self._minimum

    def groupmax(self) -> int:
        return self._maximum

    def groupmix(self) -> set[str]:
        return set(self._mix)


__all__ = ["ConfigLimits"]

"""Album diffing utilities decoupled from mutation planning."""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import Mapping, Sequence

from navigator.core.entity.media import MediaItem


@dataclass(frozen=True, slots=True)
class AlbumDiff:
    """Capture high-level album comparison outcomes."""

    retitled: bool
    reshaped: bool


class AlbumComparator:
    """Compare historic and fresh albums to detect structural changes."""

    def __init__(self, *, thumbguard: bool) -> None:
        self._thumbguard = thumbguard

    def compare(
            self,
            former_band: Sequence[MediaItem],
            latter_band: Sequence[MediaItem],
            former_info: Mapping[str, object],
            latter_info: Mapping[str, object],
    ) -> AlbumDiff:
        """Return the diff between the stored and fresh album payloads."""

        retitled = self._retitled(former_band, latter_band, former_info, latter_info)
        reshaped = self._reshaped(former_info, latter_info)
        if self._thumbguard:
            reshaped = reshaped or self._thumb_changed(former_info, latter_info)
        return AlbumDiff(retitled=retitled, reshaped=reshaped)

    @staticmethod
    def _retitled(
            former_band: Sequence[MediaItem],
            latter_band: Sequence[MediaItem],
            former_info: Mapping[str, object],
            latter_info: Mapping[str, object],
    ) -> bool:
        return (
            (former_band[0].caption or "") != (latter_band[0].caption or "")
            or AlbumComparator._encoded_caption_fields(former_info)
            != AlbumComparator._encoded_caption_fields(latter_info)
            or bool(former_info.get("show_caption_above_media"))
            != bool(latter_info.get("show_caption_above_media"))
        )

    @staticmethod
    def _reshaped(
            former_info: Mapping[str, object], latter_info: Mapping[str, object]
    ) -> bool:
        return (
            bool(former_info.get("spoiler")) != bool(latter_info.get("spoiler"))
            or AlbumComparator._ensure_int(former_info.get("start"))
            != AlbumComparator._ensure_int(latter_info.get("start"))
        )

    @staticmethod
    def _thumb_changed(
            former_info: Mapping[str, object], latter_info: Mapping[str, object]
    ) -> bool:
        return bool(former_info.get("has_thumb")) != bool(
            latter_info.get("thumb") is not None
        )

    @staticmethod
    def _encoded_caption_fields(extra: Mapping[str, object]) -> str | None:
        payload = {}
        if "mode" in extra:
            payload["mode"] = extra["mode"]
        if "entities" in extra:
            payload["entities"] = extra["entities"]
        if not payload:
            return None
        return json.dumps(payload, sort_keys=True, separators=(",", ":"))

    @staticmethod
    def _ensure_int(value: object) -> object:
        try:
            return int(value) if value is not None else None
        except Exception:  # pragma: no cover - defensive
            return value


__all__ = ["AlbumComparator", "AlbumDiff"]


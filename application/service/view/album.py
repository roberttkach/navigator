from __future__ import annotations

import json
import logging
from typing import Optional

from navigator.domain.entity.history import Message
from navigator.domain.entity.media import MediaItem
from navigator.log import LogCode, jlog
from navigator.domain.port.limits import Limits
from navigator.domain.service.rendering.album import aligned
from navigator.domain.service.rendering.helpers import match
from navigator.domain.service.rendering.decision import Decision
from navigator.domain.value.content import Payload
from navigator.domain.value.message import Scope

from .executor import EditExecutor, Execution

logger = logging.getLogger(__name__)


def _album_ids(message: Message) -> list[int]:
    return [int(message.id)] + [int(x) for x in (message.extras or [])]


def _alter(old: MediaItem, new: MediaItem) -> bool:
    if old.type != new.type:
        return True
    prior = getattr(old, "path", None)
    fresh = getattr(new, "path", None)
    return not (isinstance(prior, str) and isinstance(fresh, str) and prior == fresh)


def _clone(message: Message, identifier: int, media: MediaItem) -> Message:
    return Message(
        id=identifier,
        text=None,
        media=media,
        group=None,
        markup=message.markup,
        preview=message.preview,
        extra=message.extra,
        extras=[],
        inline=message.inline,
        automated=message.automated,
        ts=message.ts,
    )


def _clusters(latter: list[MediaItem], album: list[int]) -> list[dict]:
    result: list[dict] = []
    for index, item in enumerate(latter):
        result.append(
            {
                "medium": item.type.value,
                "file": item.path,
                "caption": item.caption if index == 0 else "",
            }
        )
    return result

class AlbumService:
    def __init__(self, executor: EditExecutor, *, limits: Limits, thumbguard: bool) -> None:
        self._executor = executor
        self._limits = limits
        self._thumbguard = thumbguard

    async def partial_update(
        self, scope: Scope, former: Message, latter: Payload
    ) -> Optional[tuple[int, list[int], dict, bool]]:
        former_group = former.group or []
        latter_group = latter.group or []

        if not (
            former_group
            and latter_group
            and aligned(former_group, latter_group, limits=self._limits)
        ):
            return None

        album = _album_ids(former)
        mutated = False

        formerinfo = former.extra or {}
        latterinfo = latter.extra or {}

        def _excerpt(data: dict | None) -> dict:
            data = data or {}
            view: dict = {}
            if "mode" in data:
                view["mode"] = data["mode"]
            if "entities" in data:
                view["entities"] = data["entities"]
            return view

        def _encode(value: dict | None) -> Optional[str]:
            if not isinstance(value, dict):
                return None
            return json.dumps(value, sort_keys=True, separators=(",", ":"))

        def _integer(value):
            try:
                return int(value) if value is not None else None
            except Exception:  # pragma: no cover - defensive
                return value

        retitled = (
            (former_group[0].caption or "") != (latter_group[0].caption or "")
            or _encode(_excerpt(formerinfo)) != _encode(_excerpt(latterinfo))
            or bool(formerinfo.get("show_caption_above_media"))
            != bool(latterinfo.get("show_caption_above_media"))
        )

        reshaped = (
            bool(formerinfo.get("spoiler")) != bool(latterinfo.get("spoiler"))
            or _integer(formerinfo.get("start")) != _integer(latterinfo.get("start"))
        )

        if self._thumbguard:
            if bool(formerinfo.get("has_thumb")) != bool(latterinfo.get("thumb") is not None):
                reshaped = True

        if retitled:
            cap = latter_group[0].caption or ""
            caption_payload = latter.morph(
                media=latter_group[0],
                group=None,
                text=("" if cap == "" else None),
            )
            execution = await self._executor.execute(
                scope,
                Decision.EDIT_MEDIA_CAPTION,
                caption_payload,
                former,
            )
            mutated = mutated or bool(execution)

        if not match(former.markup, latter.reply):
            execution = await self._executor.execute(
                scope,
                Decision.EDIT_MARKUP,
                latter,
                former,
            )
            mutated = mutated or bool(execution)

        for index, pair in enumerate(zip(former_group, latter_group)):
            past = pair[0]
            latest = pair[1]
            target_id = album[0] if index == 0 else album[index]
            altered = _alter(past, latest)
            same_path = (
                isinstance(getattr(past, "path", None), str)
                and isinstance(getattr(latest, "path", None), str)
                and getattr(past, "path") == getattr(latest, "path")
            )
            if altered or ((not altered) and reshaped and same_path):
                head = former if index == 0 else _clone(former, target_id, past)
                payload = latter.morph(media=latest, group=None)
                execution = await self._executor.execute(
                    scope,
                    Decision.EDIT_MEDIA,
                    payload,
                    head,
                )
                mutated = mutated or bool(execution)

        clusters = _clusters(latter_group, album)

        jlog(logger, logging.INFO, LogCode.ALBUM_PARTIAL_OK, count=len(album))

        return album[0], list(former.extras or []), {"kind": "group", "clusters": clusters, "inline": former.inline}, mutated


__all__ = ["AlbumService"]

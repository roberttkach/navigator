"""Coordinate album refreshes during history reconciliation."""

from __future__ import annotations

import json
import logging
from typing import Optional

from navigator.core.entity.history import Message
from navigator.core.entity.media import MediaItem
from navigator.core.port.limits import Limits
from navigator.core.service.rendering.album import aligned
from navigator.core.service.rendering.decision import Decision
from navigator.core.service.rendering.helpers import match
from navigator.core.telemetry import LogCode, Telemetry, TelemetryChannel
from navigator.core.typing.result import Cluster, GroupMeta
from navigator.core.value.content import Payload
from navigator.core.value.message import Scope

from .executor import EditExecutor


def _lineup(message: Message) -> list[int]:
    """Return identifiers associated with the stored album head."""

    return [int(message.id)] + [int(extra) for extra in (message.extras or [])]


def _changed(old: MediaItem, new: MediaItem) -> bool:
    """Report whether the replacement media changed type or identity."""

    if old.type != new.type:
        return True
    prior = getattr(old, "path", None)
    fresh = getattr(new, "path", None)
    return not (isinstance(prior, str) and isinstance(fresh, str) and prior == fresh)


def _copy(message: Message, identifier: int, media: MediaItem) -> Message:
    """Clone ``message`` while replacing media identity and identifier."""

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


def _collect(latter: list[MediaItem]) -> list[Cluster]:
    """Return cluster descriptors for the refreshed album payload."""

    clusters: list[Cluster] = []
    for index, item in enumerate(latter):
        clusters.append(
            Cluster(
                medium=item.type.value,
                file=item.path,
                caption=item.caption if index == 0 else "",
            )
        )
    return clusters


def _caption_fields(extra: dict | None) -> dict:
    """Extract caption-related metadata influencing render decisions."""

    extra = extra or {}
    view: dict = {}
    if "mode" in extra:
        view["mode"] = extra["mode"]
    if "entities" in extra:
        view["entities"] = extra["entities"]
    return view


def _encode_dict(value: dict | None) -> Optional[str]:
    """Return a canonical JSON representation used for comparisons."""

    if not isinstance(value, dict):
        return None
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def _ensure_int(value):
    """Attempt to coerce ``value`` to ``int`` when feasible."""

    try:
        return int(value) if value is not None else None
    except Exception:  # pragma: no cover - defensive
        return value


class AlbumService:
    def __init__(
            self,
            executor: EditExecutor,
            *,
            limits: Limits,
            thumbguard: bool,
            telemetry: Telemetry,
    ) -> None:
        self._executor = executor
        self._limits = limits
        self._thumbguard = thumbguard
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def refresh(
            self, scope: Scope, former: Message, latter: Payload
    ) -> Optional[tuple[int, list[int], GroupMeta, bool]]:
        """Refresh album state and emit edits when existing nodes diverge."""

        formerband = former.group or []
        latterband = latter.group or []

        if not (
                formerband
                and latterband
                and aligned(formerband, latterband, limits=self._limits)
        ):
            return None

        album = _lineup(former)
        mutated = False

        formerinfo = former.extra or {}
        latterinfo = latter.extra or {}

        retitled = (
                (formerband[0].caption or "") != (latterband[0].caption or "")
                or _encode_dict(_caption_fields(formerinfo))
                != _encode_dict(_caption_fields(latterinfo))
                or bool(formerinfo.get("show_caption_above_media"))
                != bool(latterinfo.get("show_caption_above_media"))
        )

        reshaped = (
                bool(formerinfo.get("spoiler")) != bool(latterinfo.get("spoiler"))
                or _ensure_int(formerinfo.get("start"))
                != _ensure_int(latterinfo.get("start"))
        )

        if self._thumbguard:
            if bool(formerinfo.get("has_thumb")) != bool(latterinfo.get("thumb") is not None):
                reshaped = True

        if retitled:
            cap = latterband[0].caption or ""
            captiondraft = latter.morph(
                media=latterband[0],
                group=None,
                text=("" if cap == "" else None),
            )
            execution = await self._executor.execute(
                scope,
                Decision.EDIT_MEDIA_CAPTION,
                captiondraft,
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

        for index, pair in enumerate(zip(formerband, latterband)):
            past = pair[0]
            latest = pair[1]
            target = album[0] if index == 0 else album[index]
            altered = _changed(past, latest)
            pathmatch = (
                    isinstance(getattr(past, "path", None), str)
                    and isinstance(getattr(latest, "path", None), str)
                    and getattr(past, "path") == getattr(latest, "path")
            )
            if altered or ((not altered) and reshaped and pathmatch):
                head = former if index == 0 else _copy(former, target, past)
                payload = latter.morph(media=latest, group=None)
                execution = await self._executor.execute(
                    scope,
                    Decision.EDIT_MEDIA,
                    payload,
                    head,
                )
                mutated = mutated or bool(execution)

        clusters = _collect(latterband)

        self._channel.emit(logging.INFO, LogCode.ALBUM_PARTIAL_OK, count=len(album))

        meta = GroupMeta(clusters=clusters, inline=former.inline)
        return album[0], list(former.extras or []), meta, mutated


__all__ = ["AlbumService"]

"""Coordinate album reconciliation for stored Telegram history."""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Iterable, Optional

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


@dataclass(frozen=True, slots=True)
class _AlbumDiff:
    """Capture high-level album comparison outcomes."""

    retitled: bool
    reshaped: bool


@dataclass(frozen=True, slots=True)
class AlbumMutation:
    """Describe a single edit operation required to refresh an album."""

    decision: Decision
    payload: Payload
    reference: Message


@dataclass(frozen=True, slots=True)
class AlbumRefreshPlan:
    """Capture planned album mutations and resulting metadata."""

    lineup: list[int]
    extras: list[int]
    meta: GroupMeta
    mutations: list[AlbumMutation]


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


def _collect(items: Iterable[MediaItem]) -> list[Cluster]:
    """Return cluster descriptors for the refreshed album payload."""

    clusters: list[Cluster] = []
    for index, item in enumerate(items):
        caption = item.caption if index == 0 else ""
        clusters.append(Cluster(medium=item.type.value, file=item.path, caption=caption))
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


def _compare_album(
        former_band: list[MediaItem],
        latter_band: list[MediaItem],
        former_info: dict,
        latter_info: dict,
        *,
        thumbguard: bool,
) -> _AlbumDiff:
    """Summarize structural differences between historic and fresh albums."""

    retitled = (
            (former_band[0].caption or "") != (latter_band[0].caption or "")
            or _encode_dict(_caption_fields(former_info))
            != _encode_dict(_caption_fields(latter_info))
            or bool(former_info.get("show_caption_above_media"))
            != bool(latter_info.get("show_caption_above_media"))
    )

    reshaped = (
            bool(former_info.get("spoiler")) != bool(latter_info.get("spoiler"))
            or _ensure_int(former_info.get("start"))
            != _ensure_int(latter_info.get("start"))
    )

    if thumbguard:
        reshaped = reshaped or (
                bool(former_info.get("has_thumb")) != bool(latter_info.get("thumb") is not None)
        )

    return _AlbumDiff(retitled=retitled, reshaped=reshaped)


def _should_refresh_media(altered: bool, reshaped: bool, path_match: bool) -> bool:
    """Return ``True`` when media needs refreshing or reshaping."""

    return altered or (reshaped and path_match)


class AlbumRefreshPlanner:
    """Derive album refresh plans without performing side effects."""

    def __init__(self, *, limits: Limits, thumbguard: bool) -> None:
        self._limits = limits
        self._thumbguard = thumbguard

    def prepare(self, former: Message, latter: Payload) -> Optional[AlbumRefreshPlan]:
        formerband = former.group or []
        latterband = latter.group or []

        if not (
            formerband
            and latterband
            and aligned(formerband, latterband, limits=self._limits)
        ):
            return None

        lineup = _lineup(former)
        formerinfo = former.extra or {}
        latterinfo = latter.extra or {}
        diff = _compare_album(
            formerband,
            latterband,
            formerinfo,
            latterinfo,
            thumbguard=self._thumbguard,
        )

        mutations: list[AlbumMutation] = []

        if diff.retitled:
            cap = latterband[0].caption or ""
            captiondraft = latter.morph(
                media=latterband[0],
                group=None,
                text=("" if cap == "" else None),
            )
            mutations.append(
                AlbumMutation(
                    decision=Decision.EDIT_MEDIA_CAPTION,
                    payload=captiondraft,
                    reference=former,
                )
            )

        if not match(former.markup, latter.reply):
            mutations.append(
                AlbumMutation(
                    decision=Decision.EDIT_MARKUP,
                    payload=latter,
                    reference=former,
                )
            )

        for index, pair in enumerate(zip(formerband, latterband)):
            past, latest = pair
            target = lineup[0] if index == 0 else lineup[index]
            altered = _changed(past, latest)
            pathmatch = (
                isinstance(getattr(past, "path", None), str)
                and isinstance(getattr(latest, "path", None), str)
                and getattr(past, "path") == getattr(latest, "path")
            )
            if _should_refresh_media(altered, diff.reshaped, pathmatch):
                head = former if index == 0 else _copy(former, target, past)
                payload = latter.morph(media=latest, group=None)
                mutations.append(
                    AlbumMutation(
                        decision=Decision.EDIT_MEDIA,
                        payload=payload,
                        reference=head,
                    )
                )

        clusters = _collect(latterband)
        meta = GroupMeta(clusters=clusters, inline=former.inline)

        return AlbumRefreshPlan(
            lineup=lineup,
            extras=list(former.extras or []),
            meta=meta,
            mutations=mutations,
        )


class AlbumMutationExecutor:
    """Execute album mutations with shared edit executor."""

    def __init__(self, executor: EditExecutor) -> None:
        self._executor = executor

    async def apply(self, scope: Scope, mutations: Iterable[AlbumMutation]) -> bool:
        mutated = False
        for mutation in mutations:
            execution = await self._executor.execute(
                scope,
                mutation.decision,
                mutation.payload,
                mutation.reference,
            )
            mutated = mutated or bool(execution)
        return mutated


class AlbumService:
    def __init__(
            self,
            executor: EditExecutor,
            *,
            limits: Limits,
            thumbguard: bool,
            telemetry: Telemetry,
    ) -> None:
        self._planner = AlbumRefreshPlanner(limits=limits, thumbguard=thumbguard)
        self._mutations = AlbumMutationExecutor(executor)
        self._channel: TelemetryChannel = telemetry.channel(__name__)

    async def refresh(
            self, scope: Scope, former: Message, latter: Payload
    ) -> Optional[tuple[int, list[int], GroupMeta, bool]]:
        """Refresh album state and emit edits when existing nodes diverge."""

        plan = self._planner.prepare(former, latter)
        if plan is None:
            return None

        mutated = await self._mutations.apply(scope, plan.mutations)

        self._channel.emit(
            logging.INFO,
            LogCode.ALBUM_PARTIAL_OK,
            count=len(plan.lineup),
        )

        return plan.lineup[0], plan.extras, plan.meta, mutated


__all__ = ["AlbumService"]

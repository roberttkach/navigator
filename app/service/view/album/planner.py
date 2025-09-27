"""Plan album refresh operations using dedicated collaborators."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

from navigator.core.entity.history import Message
from navigator.core.port.limits import Limits
from navigator.core.service.rendering.album import aligned
from navigator.core.typing.result import GroupMeta
from navigator.core.value.content import Payload

from .diff import AlbumComparator, AlbumDiff
from .metadata import AlbumMetadataBuilder
from .mutation_plan import AlbumMutation, AlbumMutationPlanner


@dataclass(frozen=True, slots=True)
class AlbumRefreshPlan:
    """Capture planned album mutations and resulting metadata."""

    lineup: list[int]
    extras: list[int]
    meta: GroupMeta
    mutations: list[AlbumMutation]


class AlbumRefreshPlanner:
    """Derive album refresh plans without performing side effects."""

    def __init__(
            self,
            *,
            limits: Limits,
            thumbguard: bool,
            comparator: AlbumComparator | None = None,
            metadata: AlbumMetadataBuilder | None = None,
            mutations: AlbumMutationPlanner | None = None,
    ) -> None:
        self._limits = limits
        self._comparator = comparator or AlbumComparator(thumbguard=thumbguard)
        self._metadata = metadata or AlbumMetadataBuilder()
        self._mutations = mutations or AlbumMutationPlanner()

    def prepare(self, former: Message, latter: Payload) -> Optional[AlbumRefreshPlan]:
        formerband = list(former.group or [])
        latterband = list(latter.group or [])

        if not (
            formerband
            and latterband
            and aligned(formerband, latterband, limits=self._limits)
        ):
            return None

        lineup = self._metadata.lineup(former)
        formerinfo = dict(former.extra or {})
        latterinfo = dict(latter.extra or {})
        diff = self._compare(formerband, latterband, formerinfo, latterinfo)

        mutations = self._mutations.plan(
            former=former,
            latter=latter,
            lineup=lineup,
            diff=diff,
        )
        clusters = self._metadata.clusters(latterband)
        meta = self._metadata.meta(inline=former.inline, clusters=clusters)

        return AlbumRefreshPlan(
            lineup=lineup,
            extras=list(former.extras or []),
            meta=meta,
            mutations=mutations,
        )

    def _compare(
            self,
            former_band: list,
            latter_band: list,
            former_info: dict,
            latter_info: dict,
    ) -> AlbumDiff:
        return self._comparator.compare(
            former_band,
            latter_band,
            former_info,
            latter_info,
        )


__all__ = ["AlbumMutation", "AlbumRefreshPlan", "AlbumRefreshPlanner"]


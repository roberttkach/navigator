"""Produce album mutation plans without performing side effects."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Sequence

from navigator.core.entity.history import Message
from navigator.core.entity.media import MediaItem
from navigator.core.service.rendering.decision import Decision
from navigator.core.service.rendering.helpers import match
from navigator.core.value.content import Payload

from .diff import AlbumDiff


@dataclass(frozen=True, slots=True)
class AlbumMutation:
    """Describe a single edit operation required to refresh an album."""

    decision: Decision
    payload: Payload
    reference: Message


class AlbumMutationPlanner:
    """Derive album mutations from diff results."""

    def plan(
            self,
            *,
            former: Message,
            latter: Payload,
            lineup: Sequence[int],
            diff: AlbumDiff,
    ) -> List[AlbumMutation]:
        """Return mutations required to reconcile ``former`` with ``latter``."""

        former_band = list(former.group or [])
        latter_band = list(latter.group or [])
        mutations: List[AlbumMutation] = []

        if diff.retitled and latter_band:
            mutations.append(self._retitle(former, latter, latter_band[0]))

        if not match(former.markup, latter.reply):
            mutations.append(
                AlbumMutation(
                    decision=Decision.EDIT_MARKUP,
                    payload=latter,
                    reference=former,
                )
            )

        mutations.extend(
            self._refresh_media(
                former,
                latter,
                former_band,
                latter_band,
                lineup,
                diff,
            )
        )
        return mutations

    @staticmethod
    def _retitle(
            former: Message, latter: Payload, refreshed_head: MediaItem
    ) -> AlbumMutation:
        cap = refreshed_head.caption or ""
        captiondraft = latter.morph(
            media=refreshed_head,
            group=None,
            text=("" if cap == "" else None),
        )
        return AlbumMutation(
            decision=Decision.EDIT_MEDIA_CAPTION,
            payload=captiondraft,
            reference=former,
        )

    def _refresh_media(
            self,
            former: Message,
            latter: Payload,
            former_band: Sequence[MediaItem],
            latter_band: Sequence[MediaItem],
            lineup: Sequence[int],
            diff: AlbumDiff,
    ) -> Iterable[AlbumMutation]:
        for index, pair in enumerate(zip(former_band, latter_band)):
            past, latest = pair
            target = lineup[0] if index == 0 else lineup[index]
            altered = self._changed(past, latest)
            pathmatch = (
                isinstance(getattr(past, "path", None), str)
                and isinstance(getattr(latest, "path", None), str)
                and getattr(past, "path") == getattr(latest, "path")
            )
            if self._should_refresh_media(altered, diff.reshaped, pathmatch):
                head = former if index == 0 else self._copy(former, target, past)
                payload = latter.morph(media=latest, group=None)
                yield AlbumMutation(
                    decision=Decision.EDIT_MEDIA,
                    payload=payload,
                    reference=head,
                )

    @staticmethod
    def _should_refresh_media(altered: bool, reshaped: bool, path_match: bool) -> bool:
        return altered or (reshaped and path_match)

    @staticmethod
    def _changed(old: MediaItem, new: MediaItem) -> bool:
        if old.type != new.type:
            return True
        prior = getattr(old, "path", None)
        fresh = getattr(new, "path", None)
        return not (isinstance(prior, str) and isinstance(fresh, str) and prior == fresh)

    @staticmethod
    def _copy(message: Message, identifier: int, media: MediaItem) -> Message:
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


__all__ = ["AlbumMutation", "AlbumMutationPlanner"]


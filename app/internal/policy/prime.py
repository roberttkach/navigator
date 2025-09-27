from __future__ import annotations

from dataclasses import dataclass

from navigator.core.entity.history import Entry, Message
from navigator.core.entity.media import MediaItem
from navigator.core.port.clock import Clock
from navigator.core.service.history.extra import cleanse
from navigator.core.util.entities import EntitySanitizer
from navigator.core.value.content import Payload, caption


@dataclass(slots=True)
class PrimeEntryFactory:
    """Build lightweight history entries for tail editing workflows."""

    clock: Clock
    entities: EntitySanitizer

    def create(self, identifier: int, payload: Payload) -> Entry:
        media = None
        if payload.media:
            media = MediaItem(
                type=payload.media.type,
                path=payload.media.path,
                caption=caption(payload),
            )

        length = _content_length(payload)
        extra = cleanse(payload.extra, length=length, entities=self.entities)
        message = Message(
            id=identifier,
            text=None if (payload.media or payload.group) else payload.text,
            media=media,
            group=payload.group,
            markup=None,
            preview=payload.preview,
            extra=extra,
            automated=True,
            ts=self.clock.now(),
        )
        return Entry(
            state=None,
            view=None,
            messages=[message],
        )


def _content_length(payload: Payload) -> int:
    """Return the effective caption length for ``payload`` metadata."""

    if payload.group:
        first = payload.group[0] if payload.group else None
        return len((getattr(first, "caption", None) or "")) if first else 0
    if payload.media:
        return len(caption(payload) or "")
    if isinstance(payload.text, str):
        return len(payload.text)
    return 0


def prime(
        identifier: int,
        payload: Payload,
        *,
        clock: Clock,
        entities: EntitySanitizer,
) -> Entry:
    """Compatibility wrapper around :class:`PrimeEntryFactory`."""

    return PrimeEntryFactory(clock, entities).create(identifier, payload)


__all__ = ["PrimeEntryFactory", "prime"]

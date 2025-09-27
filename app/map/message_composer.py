"""Compose message entities from payloads and rendering metadata."""
from __future__ import annotations

from datetime import datetime
from typing import Any, Iterable, Optional

from ...core.entity.history import Entry, Message
from ...core.entity.media import MediaItem
from ...core.util.entities import EntitySanitizer
from ...core.value.content import Payload
from .extra import ExtraSanitizer
from .message_content import (
    CaptionLengthCalculator,
    MessageContentResolver,
    resolve_inline,
)


class MessageComposer:
    """Compose message instances based on rendering metadata."""

    def __init__(
        self,
        *,
        outcome: "Outcome",
        base: Optional[Entry],
        timestamp: datetime,
        entities: EntitySanitizer,
    ) -> None:
        self._outcome = outcome
        self._base = base
        self._timestamp = timestamp
        self._extra = ExtraSanitizer(entities=entities)

    def build(self, index: int, payload: Payload) -> Message:
        meta = self._outcome.meta_at(index)
        inline = resolve_inline(meta)
        text, media, group = MessageContentResolver(payload).resolve(meta)
        extra = self._resolve_extra(payload, index, text, media, group)
        return Message(
            id=self._outcome.id_at(index),
            text=text,
            media=media,
            group=group,
            markup=payload.reply,
            preview=payload.preview,
            extra=extra,
            extras=self._outcome.extras_at(index),
            inline=inline,
            automated=True,
            ts=self._timestamp,
        )

    def _resolve_extra(
        self,
        payload: Payload,
        index: int,
        text: Optional[str],
        media: Optional[MediaItem],
        group: Optional[Iterable[MediaItem]],
    ) -> Optional[dict[str, Any]]:
        length = CaptionLengthCalculator.calculate(text, media, group)
        return self._extra.sanitize(payload, base=self._base, index=index, length=length)


__all__ = ["MessageComposer"]

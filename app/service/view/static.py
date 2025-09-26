"""Static payload reconstruction helpers."""

from __future__ import annotations

from typing import List, Sequence

from ....core.entity.history import Message
from ....core.value.content import Payload


class StaticPayloadFactory:
    """Transform stored messages into payload shells."""

    def build_many(self, messages: Sequence[Message]) -> List[Payload]:
        return [self.build(message) for message in messages]

    def build(self, message: Message) -> Payload:
        text = getattr(message, "text", None)
        media = getattr(message, "media", None)

        if text is None and media is not None:
            caption = getattr(media, "caption", None)
            if isinstance(caption, str) and caption:
                text = caption

        return Payload(
            text=text,
            media=media,
            group=message.group,
            reply=message.markup,
            preview=message.preview,
            extra=message.extra,
        )


__all__ = ["StaticPayloadFactory"]

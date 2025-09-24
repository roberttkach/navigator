from __future__ import annotations

from typing import Any, Optional

from navigator.domain.entity.markup import Markup
from navigator.domain.port.markup import MarkupCodec


def decode(codec: MarkupCodec, reply: Any) -> Optional[Any]:
    if isinstance(reply, Markup):
        return codec.decode(reply)
    return None


__all__ = ["decode"]

from __future__ import annotations

from navigator.core.entity.markup import Markup
from navigator.core.port.markup import MarkupCodec
from typing import Any, Optional


def decode(codec: MarkupCodec, reply: Any) -> Optional[Any]:
    if isinstance(reply, Markup):
        return codec.decode(reply)
    return None


__all__ = ["decode"]

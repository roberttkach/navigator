from __future__ import annotations

from typing import Any, Optional

from domain.entity.markup import Markup
from domain.port.markup import MarkupCodec


def decode(codec: MarkupCodec, reply: Any) -> Optional[Any]:
    if isinstance(reply, Markup):
        return codec.decode(reply)
    return None


__all__ = ["decode"]

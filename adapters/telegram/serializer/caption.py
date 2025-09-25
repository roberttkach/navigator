from __future__ import annotations

from navigator.core.value.content import Payload, caption as resolve_caption
from typing import Optional


def caption(payload: Payload) -> Optional[str]:
    return resolve_caption(payload)


def restate(payload: Payload) -> Optional[str]:
    text = resolve_caption(payload)
    if text is not None:
        return text
    if payload.erase:
        return ""
    return None


__all__ = ["caption", "restate"]

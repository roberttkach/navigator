"""Payload preservation helpers for store operations."""
from __future__ import annotations

from dataclasses import replace

from ....core.entity.history import Message
from ....core.value.content import Payload


def preserve(payload: Payload, entry: Message | None) -> Payload:
    """Return ``payload`` with preview and extra inherited from ``entry``."""

    if entry is None:
        return payload

    preview = _inherit(payload.preview, entry.preview)
    extra = _inherit(payload.extra, entry.extra)
    if preview is payload.preview and extra is payload.extra:
        return payload
    return replace(payload, preview=preview, extra=extra)


def _inherit(current: object | None, fallback: object | None) -> object | None:
    """Return ``current`` unless it is ``None``, falling back to ``fallback``."""

    return current if current is not None else fallback


__all__ = ["preserve"]

"""Context helpers for telegram retreat workflows."""

from __future__ import annotations

from typing import Any

from aiogram.types import CallbackQuery


class RetreatContextBuilder:
    """Create navigator context payloads for retreat execution."""

    def build(self, cb: CallbackQuery, payload: dict[str, Any]) -> dict[str, Any]:
        return {**payload, "event": cb}


__all__ = ["RetreatContextBuilder"]
